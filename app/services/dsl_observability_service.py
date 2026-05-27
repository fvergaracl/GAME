"""
Observability sink for DSL strategy executions (Sprint 11).

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

The service is wired with ``random.Random`` so tests can pass a
seeded instance and assert on exact rows persisted. In production the
default ``random`` module instance is used.

Persistence is best-effort: any exception from the repository is
caught and logged, never re-raised. The engine must never fail a
scoring call because a metrics row couldn't be written.
"""

from __future__ import annotations

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
    ) -> None:
        self._repository = execution_log_repository
        self._rng = rng or random

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

        try:
            await self._repository.insert_row(row)
        except Exception:
            # Persistence failure must never break scoring. Logged at
            # WARNING so it surfaces in dashboards but doesn't page.
            logger.warning(
                "Failed to persist StrategyExecutionLog for "
                "strategyId=%s status=%s",
                strategyId,
                status,
                exc_info=True,
            )


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
