"""
Sprint 10 - tests for ``StrategyObservabilityService``.

The service composes 5 narrow repository queries into one response. We
mock the repository at AsyncMock level so we can assert:

  * Status mix normalises into the schema's enum (ok/error/timeout/limit)
    and lumps unknown statuses into ``other``.
  * Percentiles are computed in Python from the duration sample and
    match what NumPy's default linear interpolation would return.
  * Success/error rates are derived from the breakdown, not re-queried.
  * A/B comparison computes B - A deltas server-side and the per-event
    points average uses the run count of each side (not totals).
  * Tenant scoping passes through to ``StrategyDefinitionService`` -
    a foreign realm propagates the 404 before any aggregation runs.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.schema.strategy_definition_schema import StrategyDefinitionRead
from app.services.strategy_observability_service import (StrategyObservabilityService,
                                                         _duration_histogram,
                                                         _percentile, _points_histogram,
                                                         _status_breakdown)


def _make_strategy(id_: str = "s1", name: str = "demo", version: int = 1):
    return StrategyDefinitionRead(
        id=id_,
        realmId="realm-a",
        name=name,
        description=None,
        type="DSL_FULL",
        parentStrategyId=None,
        astJson=None,
        blocklyXml=None,
        version=version,
        status="PUBLISHED",
        createdBy=None,
        created_at=None,
        updated_at=None,
        publishedAt=None,
        experimentTag=None,
    )


def _make_repo(
    *,
    status_counts,
    error_counts=None,
    case_counts=None,
    summary=None,
    duration_samples=None,
    points_samples=None,
):
    repo = MagicMock()
    repo.count_by_status = AsyncMock(return_value=status_counts)
    repo.count_by_error_code = AsyncMock(return_value=error_counts or [])
    repo.count_by_case_name = AsyncMock(return_value=case_counts or [])
    repo.duration_and_nodes_summary = AsyncMock(
        return_value=summary
        or {
            "count": sum(status_counts.values()),
            "durationAvgMs": 0.0,
            "durationMinMs": 0.0,
            "durationMaxMs": 0.0,
            "durationSumMs": 0.0,
            "nodesAvg": 0.0,
            "nodesMax": 0,
            "pointsSum": 0.0,
        }
    )
    repo.sample_durations = AsyncMock(return_value=duration_samples or [])
    repo.sample_points = AsyncMock(return_value=points_samples or [])
    return repo


class TestStatusBreakdown:
    def test_known_statuses_split_into_their_buckets(self):
        out = _status_breakdown({"ok": 80, "error": 10, "timeout": 5, "limit": 2})
        assert out.ok == 80
        assert out.error == 10
        assert out.timeout == 5
        assert out.limit == 2
        assert out.other == 0
        assert out.total == 97

    def test_unknown_status_lumped_into_other(self):
        # If the engine ever ships a new status code we don't know about,
        # the dashboard mustn't crash - bucket it into ``other`` instead.
        out = _status_breakdown({"ok": 1, "weird": 3})
        assert out.other == 3
        assert out.total == 4

    def test_empty_returns_zeros(self):
        out = _status_breakdown({})
        assert out.total == 0
        assert out.ok == 0


class TestPercentile:
    def test_p50_of_sorted_list(self):
        assert _percentile([10, 20, 30, 40, 50], 0.5) == 30

    def test_p95_interpolated(self):
        # NumPy: np.percentile([10,20,30,40,50], 95) = 48.0
        assert _percentile([10, 20, 30, 40, 50], 0.95) == pytest.approx(48.0)

    def test_empty_returns_zero(self):
        assert _percentile([], 0.5) == 0.0

    def test_singleton_returns_value(self):
        assert _percentile([42.0], 0.99) == 42.0


class TestDurationHistogram:
    def test_buckets_durations_onto_fixed_edges(self):
        samples = [1.0, 3.0, 8.0, 30.0, 60.0, 9999.0]
        buckets = _duration_histogram(samples)
        # Always returns len(edges)+1 buckets.
        assert len(buckets) == 13
        # The two ≤5ms samples land in the first bucket.
        assert buckets[0].count == 2
        # 9999ms falls beyond the last edge.
        assert buckets[-1].count == 1

    def test_empty_returns_all_zero_buckets(self):
        buckets = _duration_histogram([])
        assert all(b.count == 0 for b in buckets)


class TestPointsHistogram:
    def test_adaptive_buckets_span_min_to_max(self):
        samples = [0.0, 50.0, 100.0]
        buckets = _points_histogram(samples)
        assert len(buckets) == 10
        # First and last buckets are non-empty.
        assert buckets[0].count >= 1
        assert buckets[-1].count >= 1

    def test_single_value_collapses_to_one_bucket(self):
        buckets = _points_histogram([5.0, 5.0, 5.0])
        assert len(buckets) == 1
        assert buckets[0].count == 3


class TestGetMetrics:
    @pytest.mark.asyncio
    async def test_aggregates_all_repo_outputs_into_one_response(self):
        strategy = _make_strategy()
        defs_service = MagicMock()
        defs_service.get_strategy = AsyncMock(return_value=strategy)

        repo = _make_repo(
            status_counts={"ok": 80, "error": 15, "timeout": 5},
            error_counts=[
                {"code": "DSL_TIMEOUT", "count": 5},
                {"code": "DSL_ARITH_DIV_BY_ZERO", "count": 10},
            ],
            case_counts=[
                {"caseName": "BasicEngagement", "count": 50},
                {"caseName": None, "count": 30},
            ],
            summary={
                "count": 100,
                "durationAvgMs": 42.0,
                "durationMinMs": 1.0,
                "durationMaxMs": 1500.0,
                "durationSumMs": 4200.0,
                "nodesAvg": 12.5,
                "nodesMax": 200,
                "pointsSum": 175.0,
            },
            duration_samples=[10.0, 20.0, 30.0, 40.0, 50.0],
            points_samples=[1.0, 2.0, 3.0, 4.0],
        )

        svc = StrategyObservabilityService(
            execution_log_repository=repo,
            strategy_definition_service=defs_service,
        )
        result = await svc.get_metrics(id="s1", realmId="realm-a")

        # Identity + lifecycle pulled from the definition service so
        # the UI can render "v3 PUBLISHED" without a second roundtrip.
        assert result.strategyId == "s1"
        assert result.name == "demo"
        assert result.version == 1
        assert result.status == "PUBLISHED"

        # Status mix + rates derived from the breakdown counts.
        assert result.statusBreakdown.total == 100
        assert result.successRate == pytest.approx(0.80)
        assert result.errorRate == pytest.approx(0.20)

        # Percentiles match what NumPy would emit for [10..50].
        assert result.duration.p50Ms == pytest.approx(30.0)
        assert result.duration.p95Ms == pytest.approx(48.0)
        assert result.duration.sampleSize == 5
        assert result.duration.avgMs == pytest.approx(42.0)
        assert result.duration.maxMs == pytest.approx(1500.0)

        # Top-N passthroughs preserve repo order (already pre-sorted).
        assert result.topErrors[0].code == "DSL_TIMEOUT"
        assert result.topCases[1].caseName is None

        assert result.nodesAvg == pytest.approx(12.5)
        assert result.nodesMax == 200
        assert result.pointsSum == pytest.approx(175.0)

    @pytest.mark.asyncio
    async def test_404_on_strategy_propagates_before_repo_runs(self):
        # Tenant scoping: a foreign realm raises NotFoundError from the
        # definition service, and we must not spend repo queries on a
        # strategy we couldn't read.
        defs_service = MagicMock()
        defs_service.get_strategy = AsyncMock(
            side_effect=NotFoundError(detail="Custom strategy not found: s1")
        )
        repo = MagicMock()
        repo.count_by_status = AsyncMock()

        svc = StrategyObservabilityService(
            execution_log_repository=repo,
            strategy_definition_service=defs_service,
        )
        with pytest.raises(NotFoundError):
            await svc.get_metrics(id="s1", realmId="other-realm")
        repo.count_by_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_window_yields_zero_rates_not_division_error(self):
        # With no recorded executions every rate is 0, not a DBZ. The
        # dashboard renders the "no data" empty state off ``total == 0``.
        defs_service = MagicMock()
        defs_service.get_strategy = AsyncMock(return_value=_make_strategy())
        repo = _make_repo(status_counts={})
        svc = StrategyObservabilityService(
            execution_log_repository=repo,
            strategy_definition_service=defs_service,
        )
        result = await svc.get_metrics(id="s1", realmId="realm-a")
        assert result.statusBreakdown.total == 0
        assert result.successRate == 0.0
        assert result.errorRate == 0.0


class TestCompare:
    @pytest.mark.asyncio
    async def test_delta_is_b_minus_a(self):
        # A: 80% ok, B: 90% ok → +10pp success delta. Latency P95 lower
        # on B (positive sense: faster). Average points are computed
        # *per run*, not from raw sums, so different run counts don't
        # bias the delta.
        strategy_a = _make_strategy(id_="a", name="a")
        strategy_b = _make_strategy(id_="b", name="b")

        def make_service(strategy_a_metrics, strategy_b_metrics):
            defs_service = MagicMock()
            # Return different strategies on consecutive calls.
            defs_service.get_strategy = AsyncMock(side_effect=[strategy_a, strategy_b])
            repo = MagicMock()
            # Cycle through (A's queries, then B's queries). The order
            # mirrors what _build_response calls per snapshot.
            repo.count_by_status = AsyncMock(
                side_effect=[
                    {"ok": 80, "error": 20},
                    {"ok": 90, "error": 10},
                ]
            )
            repo.count_by_error_code = AsyncMock(side_effect=[[], []])
            repo.count_by_case_name = AsyncMock(side_effect=[[], []])
            repo.duration_and_nodes_summary = AsyncMock(
                side_effect=[
                    {
                        "count": 100,
                        "durationAvgMs": 50.0,
                        "durationMinMs": 0.0,
                        "durationMaxMs": 500.0,
                        "durationSumMs": 5000.0,
                        "nodesAvg": 10.0,
                        "nodesMax": 100,
                        "pointsSum": 200.0,
                    },
                    {
                        "count": 100,
                        "durationAvgMs": 30.0,
                        "durationMinMs": 0.0,
                        "durationMaxMs": 200.0,
                        "durationSumMs": 3000.0,
                        "nodesAvg": 8.0,
                        "nodesMax": 80,
                        "pointsSum": 300.0,
                    },
                ]
            )
            repo.sample_durations = AsyncMock(
                side_effect=[
                    [40.0, 50.0, 60.0, 70.0, 80.0],
                    [20.0, 25.0, 30.0, 35.0, 40.0],
                ]
            )
            repo.sample_points = AsyncMock(side_effect=[[], []])
            return repo, defs_service

        repo, defs_service = make_service(strategy_a, strategy_b)
        svc = StrategyObservabilityService(
            execution_log_repository=repo,
            strategy_definition_service=defs_service,
        )

        result = await svc.compare(idA="a", idB="b", realmId="realm-a")

        assert result.a.successRate == pytest.approx(0.80)
        assert result.b.successRate == pytest.approx(0.90)
        # B - A success rate
        assert result.delta.successRate == pytest.approx(0.10)
        # Latency goes down → negative delta (B is faster).
        assert result.delta.avgMs == pytest.approx(-20.0)
        # avg points per run = pointsSum / total.
        # A: 200/100 = 2.0, B: 300/100 = 3.0 → delta = +1.0
        assert result.delta.pointsAvg == pytest.approx(1.0)
