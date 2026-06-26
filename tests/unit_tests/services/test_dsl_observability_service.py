"""
Sprint 11 - sampled persistence + metrics emission for DSL executions.

The observer is the bridge between ``DslStrategy.calculate_points`` and
two side-channels: the Prometheus registry and the
``strategyexecutionlog`` table. These tests pin the sampler logic
(errors always kept, ok runs sampled by random seed) and the trace
truncation behaviour. Metrics emission is validated separately by
inspecting the global registry.
"""

from __future__ import annotations

import random
import unittest
from unittest.mock import AsyncMock

from app.services.dsl_observability_service import (
    DslExecutionObserver,
    NoopDslExecutionObserver,
    _truncate_trace,
)


class _RecordingRepo:
    def __init__(self) -> None:
        self.rows = []

    async def insert_row(self, row):
        self.rows.append(row)


class TestTraceTruncation(unittest.TestCase):
    def test_none_passes_through(self):
        self.assertIsNone(_truncate_trace(None, 10))

    def test_under_limit_returns_copy(self):
        trace = [{"nodeId": "a"}, {"nodeId": "b"}]
        out = _truncate_trace(trace, 10)
        self.assertEqual(out, trace)
        self.assertIsNot(out, trace)

    def test_over_limit_keeps_head(self):
        trace = [{"nodeId": str(i)} for i in range(100)]
        out = _truncate_trace(trace, 10)
        self.assertEqual(len(out), 10)
        self.assertEqual(out[0]["nodeId"], "0")
        self.assertEqual(out[-1]["nodeId"], "9")

    def test_non_positive_limit_disables_truncation(self):
        trace = [{"nodeId": str(i)} for i in range(100)]
        out = _truncate_trace(trace, 0)
        self.assertEqual(len(out), 100)


class TestObserverPersistence(unittest.IsolatedAsyncioTestCase):
    async def test_error_row_always_persisted_regardless_of_sample_rate(self):
        # Force the sample rate to 0 to prove errors bypass the sampler.
        from app.core.config import configs as live

        original = live.DSL_EXECUTION_LOG_SAMPLE_RATE
        live.DSL_EXECUTION_LOG_SAMPLE_RATE = 0.0
        try:
            repo = _RecordingRepo()
            observer = DslExecutionObserver(
                execution_log_repository=repo,
                rng=random.Random(0),
            )
            await observer.record(
                strategyId="s1",
                strategyVersion=1,
                strategyType="DSL_FULL",
                realmId="realm-a",
                externalGameId="g",
                externalTaskId="t",
                externalUserId="u",
                status="timeout",
                errorCode="DSL_TIMEOUT",
                points=None,
                caseName=None,
                durationMs=750.5,
                nodesExecuted=999,
                trace=[{"nodeId": "x"}],
            )
            # Sprint 13: persistence is now drained by a background
            # worker; wait for it before asserting on the rows.
            await observer.drain()
            self.assertEqual(len(repo.rows), 1)
            row = repo.rows[0]
            self.assertEqual(row.status, "timeout")
            self.assertEqual(row.errorCode, "DSL_TIMEOUT")
            # Error rows are NOT sampled rows -- the sampled flag exists
            # so the runbook can quickly split "kept by sampler" from
            # "kept because failure".
            self.assertFalse(row.sampled)
        finally:
            live.DSL_EXECUTION_LOG_SAMPLE_RATE = original

    async def test_ok_run_kept_when_sampler_hits(self):
        # Seed an rng whose first random() call returns < 0.5.
        rng = random.Random(0)
        # random.Random(0).random() ~ 0.844 -- so use a rate above that
        # to guarantee a hit.
        from app.core.config import configs as live

        original = live.DSL_EXECUTION_LOG_SAMPLE_RATE
        live.DSL_EXECUTION_LOG_SAMPLE_RATE = 0.99
        try:
            repo = _RecordingRepo()
            observer = DslExecutionObserver(
                execution_log_repository=repo,
                rng=rng,
            )
            await observer.record(
                strategyId="s2",
                strategyVersion=3,
                strategyType="DSL_EXTEND",
                realmId="realm-a",
                externalGameId="g",
                externalTaskId="t",
                externalUserId="u",
                status="ok",
                errorCode=None,
                points=1.5,
                caseName="BasicEngagement",
                durationMs=12.0,
                nodesExecuted=8,
                trace=[{"nodeId": "x"}],
                parentStrategyId="default",
            )
            await observer.drain()
            self.assertEqual(len(repo.rows), 1)
            row = repo.rows[0]
            self.assertEqual(row.status, "ok")
            self.assertTrue(row.sampled)
            self.assertEqual(row.parentStrategyId, "default")
            self.assertEqual(row.strategyVersion, 3)
        finally:
            live.DSL_EXECUTION_LOG_SAMPLE_RATE = original

    async def test_ok_run_skipped_when_sampler_misses(self):
        # Rate 0 ⇒ no ok run is persisted.
        from app.core.config import configs as live

        original = live.DSL_EXECUTION_LOG_SAMPLE_RATE
        live.DSL_EXECUTION_LOG_SAMPLE_RATE = 0.0
        try:
            repo = _RecordingRepo()
            observer = DslExecutionObserver(
                execution_log_repository=repo,
                rng=random.Random(0),
            )
            await observer.record(
                strategyId="s3",
                strategyVersion=1,
                strategyType="DSL_FULL",
                realmId="realm-a",
                externalGameId=None,
                externalTaskId=None,
                externalUserId=None,
                status="ok",
                errorCode=None,
                points=1.0,
                caseName="X",
                durationMs=5.0,
                nodesExecuted=3,
                trace=[],
            )
            self.assertEqual(repo.rows, [])
        finally:
            live.DSL_EXECUTION_LOG_SAMPLE_RATE = original

    async def test_log_disabled_skips_persistence(self):
        from app.core.config import configs as live

        original_enabled = live.DSL_EXECUTION_LOG_ENABLED
        live.DSL_EXECUTION_LOG_ENABLED = False
        try:
            repo = _RecordingRepo()
            observer = DslExecutionObserver(
                execution_log_repository=repo,
                rng=random.Random(0),
            )
            # Even an error row is dropped when the feature flag is off.
            await observer.record(
                strategyId="s4",
                strategyVersion=1,
                strategyType="DSL_FULL",
                realmId="realm-a",
                externalGameId=None,
                externalTaskId=None,
                externalUserId=None,
                status="error",
                errorCode="DSL_ARITH_DIV_BY_ZERO",
                points=None,
                caseName=None,
                durationMs=2.0,
                nodesExecuted=4,
                trace=[],
            )
            self.assertEqual(repo.rows, [])
        finally:
            live.DSL_EXECUTION_LOG_ENABLED = original_enabled

    async def test_no_repository_skips_persistence_without_raising(self):
        # Legacy code path: tests that instantiate DslStrategy directly
        # don't wire a repository. The observer must not blow up.
        observer = DslExecutionObserver(
            execution_log_repository=None,
            rng=random.Random(0),
        )
        await observer.record(
            strategyId="s5",
            strategyVersion=1,
            strategyType="DSL_FULL",
            realmId=None,
            externalGameId=None,
            externalTaskId=None,
            externalUserId=None,
            status="ok",
            errorCode=None,
            points=0,
            caseName=None,
            durationMs=0.1,
            nodesExecuted=0,
            trace=[],
        )

    async def test_persistence_failure_does_not_propagate(self):
        # If the repository raises, the observer must swallow so a
        # broken sink never breaks scoring.
        from app.core.config import configs as live

        original = live.DSL_EXECUTION_LOG_SAMPLE_RATE
        live.DSL_EXECUTION_LOG_SAMPLE_RATE = 0.0
        try:
            repo = AsyncMock()
            repo.insert_row.side_effect = RuntimeError("db down")
            observer = DslExecutionObserver(
                execution_log_repository=repo,
                rng=random.Random(0),
            )
            # Errors are always sampled, so the insert is attempted.
            await observer.record(
                strategyId="s6",
                strategyVersion=1,
                strategyType="DSL_FULL",
                realmId=None,
                externalGameId=None,
                externalTaskId=None,
                externalUserId=None,
                status="error",
                errorCode="DSL_ARITH_DIV_BY_ZERO",
                points=None,
                caseName=None,
                durationMs=2.0,
                nodesExecuted=4,
                trace=None,
            )
            # Drain so the worker attempts (and swallows) the insert.
            await observer.drain()
            repo.insert_row.assert_awaited_once()
        finally:
            live.DSL_EXECUTION_LOG_SAMPLE_RATE = original


class TestObserverQueue(unittest.IsolatedAsyncioTestCase):
    """Sprint 13 - the DB write is drained off the hot-path by a
    background worker fed from a bounded queue."""

    async def _record_error(self, observer, *, strategyId="q1"):
        # Errors are always persisted, so this reliably enqueues a row
        # without depending on the sampler.
        await observer.record(
            strategyId=strategyId,
            strategyVersion=1,
            strategyType="DSL_FULL",
            realmId="realm-q",
            externalGameId=None,
            externalTaskId=None,
            externalUserId=None,
            status="error",
            errorCode="DSL_TEST",
            points=None,
            caseName=None,
            durationMs=1.0,
            nodesExecuted=1,
            trace=None,
        )

    async def test_record_does_not_block_on_db(self):
        # The worker drains asynchronously; record returns before the
        # insert has run. Only after draining are the rows present.
        repo = _RecordingRepo()
        observer = DslExecutionObserver(
            execution_log_repository=repo,
            rng=random.Random(0),
        )
        await self._record_error(observer)
        # No await point yielded to the worker yet → not persisted.
        self.assertEqual(repo.rows, [])
        await observer.drain()
        self.assertEqual(len(repo.rows), 1)
        await observer.aclose()

    async def test_full_queue_drops_and_counts(self):
        before = _scrape_dropped().get(("realm-q", "DSL_FULL"), 0)
        repo = _RecordingRepo()
        observer = DslExecutionObserver(
            execution_log_repository=repo,
            rng=random.Random(0),
            queue_maxsize=1,
        )
        # Two enqueues back-to-back with no yielding await between them:
        # the worker never gets scheduled, so the second hits a full
        # queue and is dropped + counted.
        await self._record_error(observer, strategyId="keep")
        await self._record_error(observer, strategyId="dropped")
        after = _scrape_dropped().get(("realm-q", "DSL_FULL"), 0)
        self.assertEqual(after - before, 1)
        await observer.drain()
        # Exactly the first row survived.
        self.assertEqual([r.strategyId for r in repo.rows], ["keep"])
        await observer.aclose()

    async def test_aclose_flushes_and_is_idempotent(self):
        repo = _RecordingRepo()
        observer = DslExecutionObserver(
            execution_log_repository=repo,
            rng=random.Random(0),
        )
        await self._record_error(observer)
        await observer.aclose()
        self.assertEqual(len(repo.rows), 1)
        # Second close is a no-op and further records are dropped.
        await observer.aclose()
        await self._record_error(observer)
        self.assertEqual(len(repo.rows), 1)


class TestObserverMetrics(unittest.IsolatedAsyncioTestCase):
    async def test_metrics_increment_on_record(self):
        # Read counter samples by name from the global registry. We
        # don't compare absolute values (other tests may have
        # incremented them) -- we compare delta around our own call.
        # Note: prometheus_client strips the ``_total`` suffix from
        # counter metric.name, so we look up the base name.
        before = _scrape("dsl_execution_errors")
        observer = DslExecutionObserver(
            execution_log_repository=None,
            rng=random.Random(0),
        )
        await observer.record(
            strategyId="s7",
            strategyVersion=1,
            strategyType="DSL_FULL",
            realmId="realm-metrics-test",
            externalGameId=None,
            externalTaskId=None,
            externalUserId=None,
            status="error",
            errorCode="DSL_TEST",
            points=None,
            caseName=None,
            durationMs=10.0,
            nodesExecuted=5,
            trace=None,
        )
        after = _scrape("dsl_execution_errors")
        # Our specific (realm, code) combination must have at least one
        # observation after the call.
        key = (
            "realm-metrics-test",
            "DSL_FULL",
            "DSL_TEST",
        )
        self.assertGreaterEqual(after.get(key, 0), 1)
        self.assertGreater(after.get(key, 0), before.get(key, 0))


class TestNoopObserver(unittest.IsolatedAsyncioTestCase):
    async def test_noop_observer_drops_everything(self):
        observer = NoopDslExecutionObserver()
        # Should not raise regardless of kwargs.
        await observer.record(anything="goes", here=42)


def _scrape(metric_name: str):
    """
    Read the global Prometheus default registry into a
    {label-tuple: value} dict for the metric of interest.
    """
    from prometheus_client import REGISTRY

    out = {}
    for metric in REGISTRY.collect():
        if metric.name != metric_name:
            continue
        for sample in metric.samples:
            if not sample.name.endswith("_total"):
                continue
            labels = tuple(
                sample.labels.get(k) for k in ("realm", "strategy_type", "code")
            )
            out[labels] = sample.value
    return out


def _scrape_dropped():
    """Read ``dsl_execution_log_dropped_total`` into a
    {(realm, strategy_type): value} dict."""
    from prometheus_client import REGISTRY

    out = {}
    for metric in REGISTRY.collect():
        if metric.name != "dsl_execution_log_dropped":
            continue
        for sample in metric.samples:
            if not sample.name.endswith("_total"):
                continue
            labels = (
                sample.labels.get("realm"),
                sample.labels.get("strategy_type"),
            )
            out[labels] = sample.value
    return out


if __name__ == "__main__":
    unittest.main()
