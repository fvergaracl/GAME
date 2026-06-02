"""
Observability sink for DSL strategy executions (Sprint 11, Sprint 13).

This service does *two* things for every ``DslStrategy.calculate_points``
call (the wiring lives in :mod:`app.engine.dsl_strategy`):

1. Emits the Prometheus metrics defined in
   :mod:`app.engine.dsl_metrics`. Always synchronous, always cheap;
   never blocks scoring.

2. Persists a row to ``strategyexecutionlog`` when the sampler picks
   the run or when the run failed. Errors are *always* kept so a
   post-mortem can replay the input via ``/simulate`` even months
   after the incident. OK runs are sampled at
   :data:`_config_module.configs.DSL_EXECUTION_LOG_SAMPLE_RATE` (default 5 %).

Sprint 13 — hot-path: ``record`` no longer ``await``\\s the DB write.
The metrics emit + sampling decision stay synchronous (microseconds),
and the chosen row is handed to a bounded in-process queue drained by a
background worker task. Scoring therefore pays only the enqueue, never a
DB round-trip. If the worker falls behind and the queue fills (a slow or
down database), rows are dropped and counted via
``dsl_execution_log_dropped_total`` rather than blocking the scoring
call — the audit log is best-effort by design. Call :meth:`aclose`
on shutdown to flush the queue and stop the worker cleanly.

The service is wired with ``random.Random`` so tests can pass a
seeded instance and assert on exact rows persisted. In production the
default ``random`` module instance is used.

Persistence is best-effort: any exception from the repository is
caught and logged, never re-raised. The engine must never fail a
scoring call because a metrics row couldn't be written.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Dict, List, Optional

# Imported as a module rather than via ``from .. import configs`` so the
# observer always sees the live ``configs`` object even when a test
# reloads ``app.core.config`` (which rebinds the symbol at module level
# but leaves any direct imports pointing at the stale instance).
from app.core import config as _config_module
from app.engine import dsl_metrics
from app.model.strategy_execution_log import StrategyExecutionLog
from app.repository.strategy_execution_log_repository import (
    StrategyExecutionLogRepository,
)

logger = logging.getLogger(__name__)


class DslExecutionObserver:
    """
    Lives as a long-lived dependency (one per process is fine -- it is
    stateless aside from the rng + repository pointer). Injected into
    ``DslStrategy`` via the container so tests can swap a no-op
    implementation.
    """

    def __init__(
        self,
        execution_log_repository: Optional[
            StrategyExecutionLogRepository
        ] = None,
        *,
        rng: Optional[random.Random] = None,
        queue_maxsize: Optional[int] = None,
    ) -> None:
        self._repository = execution_log_repository
        self._rng = rng or random
        # Sprint 13: lazily-created bounded queue + drain worker. Both are
        # created on the first enqueue (which always happens inside the
        # running event loop), so constructing the observer outside a loop
        # — as the DI container Singleton does at import time — is safe.
        self._queue_maxsize = (
            queue_maxsize
            if queue_maxsize is not None
            else _config_module.configs.DSL_EXECUTION_LOG_QUEUE_MAXSIZE
        )
        self._queue: Optional["asyncio.Queue[StrategyExecutionLog]"] = None
        self._worker: Optional[asyncio.Task] = None
        self._closed = False

    async def record(
        self,
        *,
        strategyId: str,
        strategyVersion: int,
        strategyType: str,
        realmId: Optional[str],
        externalGameId: Optional[str],
        externalTaskId: Optional[str],
        externalUserId: Optional[str],
        status: str,
        errorCode: Optional[str],
        points: Optional[float],
        caseName: Optional[str],
        durationMs: float,
        nodesExecuted: int,
        trace: Optional[List[Dict[str, Any]]],
        parentStrategyId: Optional[str] = None,
    ) -> None:
        """
        Single entry point called by ``DslStrategy._run_phase`` once
        every execution finishes (success or failure).

        ``durationMs`` is the *wall-clock* time including precompute,
        not just the interpreter walk, because that is what the SLO
        speaks to ("a scoring event taking >250ms is user-visible").
        """
        # --- metrics ------------------------------------------------
        try:
            dsl_metrics.observe(
                realm=realmId,
                strategy_type=strategyType,
                status=status,
                duration_seconds=durationMs / 1000.0,
                nodes_executed=nodesExecuted,
                error_code=errorCode,
            )
        except Exception:  # pragma: no cover - defensive
            logger.exception(
                "Failed to emit DSL metrics for strategyId=%s status=%s",
                strategyId,
                status,
            )

        # --- sampled persistence ------------------------------------
        if not _config_module.configs.DSL_EXECUTION_LOG_ENABLED:
            return
        if self._repository is None:
            # Light call sites (legacy tests) don't wire the repo; that
            # is fine -- metrics still flow, persistence simply skips.
            return

        is_error = status != "ok"
        sample_rate = _config_module.configs.DSL_EXECUTION_LOG_SAMPLE_RATE
        # Always keep errors; sample OK runs.
        should_persist = is_error or (
            sample_rate > 0
            and self._rng.random() < sample_rate
        )
        if not should_persist:
            return

        truncated_trace = _truncate_trace(
            trace, _config_module.configs.DSL_EXECUTION_LOG_TRACE_LIMIT
        )
        notes = None
        if trace is not None and len(trace) > len(truncated_trace or []):
            notes = (
                f"trace truncated: {len(trace)} -> "
                f"{len(truncated_trace)} entries"
            )

        row = StrategyExecutionLog(
            strategyId=strategyId,
            strategyVersion=strategyVersion,
            strategyType=strategyType,
            realmId=realmId,
            externalGameId=externalGameId,
            externalTaskId=externalTaskId,
            externalUserId=externalUserId,
            status=status,
            errorCode=errorCode,
            points=points,
            caseName=caseName,
            durationMs=durationMs,
            nodesExecuted=nodesExecuted,
            trace=truncated_trace,
            sampled=not is_error,
            parentStrategyId=parentStrategyId,
            notes=notes,
        )

        # Sprint 13: hand off to the background worker instead of awaiting
        # the DB write here. ``_enqueue`` never blocks and never raises —
        # a full queue drops the row (counted) so a slow database can't
        # apply backpressure to the scoring hot-path.
        self._enqueue(row, realmId=realmId, strategyType=strategyType)

    # ------------------------------------------------------------------
    # Sprint 13 — background drain worker.
    # ------------------------------------------------------------------

    def _enqueue(
        self,
        row: StrategyExecutionLog,
        *,
        realmId: Optional[str],
        strategyType: str,
    ) -> None:
        """Best-effort, non-blocking handoff to the drain worker."""
        if self._closed:
            return
        self._ensure_worker()
        try:
            self._queue.put_nowait(row)
        except asyncio.QueueFull:
            # The worker is behind (DB slow/down). Drop rather than wait:
            # scoring must never block on the audit log. Surface the drop
            # so a saturated sink is visible instead of silent data loss.
            dsl_metrics.observe_log_dropped(
                realm=realmId, strategy_type=strategyType,
            )
            logger.warning(
                "DSL execution-log queue full (maxsize=%s); dropped a "
                "row for realm=%s type=%s",
                self._queue_maxsize,
                realmId,
                strategyType,
            )

    def _ensure_worker(self) -> None:
        """Create the queue + drain task on first use, inside the loop."""
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=max(self._queue_maxsize, 1))
        if self._worker is None or self._worker.done():
            self._worker = asyncio.ensure_future(self._drain_loop())

    async def _drain_loop(self) -> None:
        assert self._queue is not None
        while True:
            row = await self._queue.get()
            try:
                await self._repository.insert_row(row)
            except Exception:
                # Persistence failure must never escape the worker.
                # Logged at WARNING so it surfaces in dashboards but
                # doesn't page; the next row keeps draining.
                logger.warning(
                    "Failed to persist StrategyExecutionLog for "
                    "strategyId=%s status=%s",
                    getattr(row, "strategyId", None),
                    getattr(row, "status", None),
                    exc_info=True,
                )
            finally:
                self._queue.task_done()

    async def drain(self) -> None:
        """Block until every queued row has been processed.

        Mainly for tests and graceful shutdown — production scoring never
        calls this. No-op if nothing has been enqueued yet.
        """
        if self._queue is not None:
            await self._queue.join()

    async def aclose(self) -> None:
        """Flush pending rows and stop the worker. Idempotent.

        Wired into the FastAPI lifespan so an orderly shutdown doesn't
        lose buffered execution logs.
        """
        self._closed = True
        await self.drain()
        if self._worker is not None and not self._worker.done():
            self._worker.cancel()
            try:
                await self._worker
            except (asyncio.CancelledError, Exception):
                pass
        self._worker = None


def _truncate_trace(
    trace: Optional[List[Dict[str, Any]]], limit: int,
) -> Optional[List[Dict[str, Any]]]:
    """
    Keep the head of the trace (where rule matching happens) and drop
    the tail when the program is long. Limit <= 0 disables truncation
    so tests can persist full traces deterministically.
    """
    if trace is None:
        return None
    if limit <= 0 or len(trace) <= limit:
        return list(trace)
    return list(trace[:limit])


class NoopDslExecutionObserver:
    """
    Placeholder observer used when the engine is exercised outside
    the DI container (e.g. raw unit tests that instantiate
    ``DslStrategy`` directly). Drops everything on the floor.
    """

    async def record(self, **_: Any) -> None:
        return None
