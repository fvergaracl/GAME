"""
Observability aggregation service (Sprint 10).

Reads from the same ``strategyexecutionlog`` table the engine writes
via :class:`DslExecutionObserver` and shapes it into the metrics view
the dashboard renders for a single strategy, plus the A/B comparison
endpoint that runs the same aggregation against two ids and computes
deltas.

The repository already does the heavy lifting (SUM/COUNT/GROUP BY in
the DB); this service is responsible for:

  * Combining 5 narrow queries into one response — the dashboard fetches
    once per page load.
  * Computing percentiles + histograms in Python from a bounded sample,
    because SQLite (used in tests) doesn't have ``percentile_cont`` and
    PostgreSQL's window-function variant is expensive on tables with
    millions of rows.
  * Tenant scoping: callers pass the strategy id, we resolve it via
    :class:`StrategyDefinitionService.get_strategy` which 404s on
    cross-realm probes, so this service is implicitly tenant-aware.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from app.repository.strategy_execution_log_repository import \
    StrategyExecutionLogRepository
from app.schema.strategy_definition_schema import StrategyDefinitionRead
from app.schema.strategy_observability_schema import (CaseCount, DurationPercentiles,
                                                      ErrorCount, HistogramBucket,
                                                      MetricsDelta, StatusBreakdown,
                                                      StrategyComparisonResponse,
                                                      StrategyMetricsResponse)
from app.services.strategy_definition_service import StrategyDefinitionService

# Bucket edges chosen to align with the Prometheus histogram in
# ``dsl_metrics.DSL_LATENCY_BUCKETS`` so the dashboard's view of a
# strategy is consistent with what the on-call alert sees. Last bucket
# is "5 s and beyond" because anything past that has already tripped a
# DSL_TIMEOUT, where time stops being meaningful.
_DURATION_BUCKETS_MS = (
    5.0,
    10.0,
    25.0,
    50.0,
    100.0,
    150.0,
    200.0,
    250.0,
    500.0,
    1000.0,
    2500.0,
    5000.0,
)


def _percentile(sorted_values: List[float], pct: float) -> float:
    """Linear-interpolation percentile over a pre-sorted list. Matches
    NumPy's default behaviour so test expectations line up with what
    ops would see in Grafana."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * pct
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def _duration_histogram(samples: List[float]) -> List[HistogramBucket]:
    """Bucket a sample of durations onto :data:`_DURATION_BUCKETS_MS`."""
    counts = [0] * (len(_DURATION_BUCKETS_MS) + 1)
    for v in samples:
        placed = False
        for i, edge in enumerate(_DURATION_BUCKETS_MS):
            if v <= edge:
                counts[i] += 1
                placed = True
                break
        if not placed:
            counts[-1] += 1
    buckets: List[HistogramBucket] = []
    prev = 0.0
    for i, edge in enumerate(_DURATION_BUCKETS_MS):
        buckets.append(
            HistogramBucket(
                label=f"≤{int(edge) if edge >= 1 else edge}ms",
                upperBound=edge,
                count=counts[i],
            )
        )
        prev = edge
    buckets.append(
        HistogramBucket(
            label=f">{int(prev)}ms",
            upperBound=None,
            count=counts[-1],
        )
    )
    return buckets


def _points_histogram(samples: List[float]) -> List[HistogramBucket]:
    """
    Adaptive bucketing for the points distribution: we don't know the
    range a priori (some strategies emit fractions, others whole
    hundreds), so derive 10 evenly-spaced bins from min..max. Falls
    back to a single all-zeros bucket when the sample is empty.
    """
    if not samples:
        return [HistogramBucket(label="0", upperBound=0.0, count=0)]
    lo = min(samples)
    hi = max(samples)
    if hi <= lo:
        return [
            HistogramBucket(
                label=f"{lo:g}",
                upperBound=lo,
                count=len(samples),
            )
        ]
    n_buckets = 10
    width = (hi - lo) / n_buckets
    counts = [0] * n_buckets
    for v in samples:
        idx = int((v - lo) / width)
        if idx >= n_buckets:
            idx = n_buckets - 1
        counts[idx] += 1
    out: List[HistogramBucket] = []
    for i in range(n_buckets):
        upper = lo + width * (i + 1)
        out.append(
            HistogramBucket(
                label=f"{lo + width * i:g}–{upper:g}",
                upperBound=upper,
                count=counts[i],
            )
        )
    return out


def _status_breakdown(raw: dict) -> StatusBreakdown:
    """Normalise the repo's free-form ``{status: count}`` map onto the
    enum the dashboard expects, lumping anything unrecognised into
    ``other`` so a new status code doesn't blow up the chart."""
    known = {"ok", "error", "timeout", "limit"}
    ok = int(raw.get("ok", 0))
    error = int(raw.get("error", 0))
    timeout = int(raw.get("timeout", 0))
    limit = int(raw.get("limit", 0))
    other = sum(int(v) for k, v in raw.items() if k not in known)
    total = ok + error + timeout + limit + other
    return StatusBreakdown(
        ok=ok,
        error=error,
        timeout=timeout,
        limit=limit,
        other=other,
        total=total,
    )


class StrategyObservabilityService:
    """Single entrypoint for the Sprint 10 dashboard view + A/B view."""

    def __init__(
        self,
        execution_log_repository: StrategyExecutionLogRepository,
        strategy_definition_service: StrategyDefinitionService,
    ) -> None:
        self._repo = execution_log_repository
        self._strategy_definition_service = strategy_definition_service

    async def get_metrics(
        self,
        *,
        id: str,
        realmId: Optional[str],
        sinceDt: Optional[datetime] = None,
        untilDt: Optional[datetime] = None,
    ) -> StrategyMetricsResponse:
        """Build the per-strategy metrics card.

        Resolves the strategy first so the response includes name +
        version + status — and so cross-realm probes 404 before we
        spend a query on the execution log.
        """
        strategy = await self._strategy_definition_service.get_strategy(
            id=id, realmId=realmId
        )
        return await self._build_response(
            strategy=strategy,
            sinceDt=sinceDt,
            untilDt=untilDt,
        )

    async def compare(
        self,
        *,
        idA: str,
        idB: str,
        realmId: Optional[str],
        sinceDt: Optional[datetime] = None,
        untilDt: Optional[datetime] = None,
    ) -> StrategyComparisonResponse:
        """Run the metrics aggregation twice in parallel-ish (awaited
        sequentially since each takes ~5 narrow queries) and compute
        deltas server-side. Both ids are validated through the same
        get_strategy path so neither can leak from a foreign realm."""
        a = await self.get_metrics(
            id=idA, realmId=realmId, sinceDt=sinceDt, untilDt=untilDt
        )
        b = await self.get_metrics(
            id=idB, realmId=realmId, sinceDt=sinceDt, untilDt=untilDt
        )
        # Per-run averages. Sum of points is meaningless for direct
        # comparison when run counts differ; the per-event average is
        # the apples-to-apples number.
        avg_points_a = (
            a.pointsSum / a.statusBreakdown.total if a.statusBreakdown.total else 0.0
        )
        avg_points_b = (
            b.pointsSum / b.statusBreakdown.total if b.statusBreakdown.total else 0.0
        )
        delta = MetricsDelta(
            successRate=b.successRate - a.successRate,
            errorRate=b.errorRate - a.errorRate,
            p95Ms=b.duration.p95Ms - a.duration.p95Ms,
            avgMs=b.duration.avgMs - a.duration.avgMs,
            pointsAvg=avg_points_b - avg_points_a,
        )
        return StrategyComparisonResponse(a=a, b=b, delta=delta)

    async def _build_response(
        self,
        *,
        strategy: StrategyDefinitionRead,
        sinceDt: Optional[datetime],
        untilDt: Optional[datetime],
    ) -> StrategyMetricsResponse:
        # Strategy executions persist with the bare definition id
        # (StrategyDefinitionLog.strategyId — see how the observer is
        # called from DslStrategy._run_phase). We pass that id verbatim
        # rather than the assignable ``custom:<uuid>`` form.
        strat_id = strategy.id
        status_raw = await self._repo.count_by_status(
            strategyId=strat_id, sinceDt=sinceDt, untilDt=untilDt
        )
        top_errors = await self._repo.count_by_error_code(
            strategyId=strat_id, sinceDt=sinceDt, untilDt=untilDt
        )
        top_cases = await self._repo.count_by_case_name(
            strategyId=strat_id, sinceDt=sinceDt, untilDt=untilDt
        )
        summary = await self._repo.duration_and_nodes_summary(
            strategyId=strat_id, sinceDt=sinceDt, untilDt=untilDt
        )
        duration_samples = await self._repo.sample_durations(
            strategyId=strat_id, sinceDt=sinceDt, untilDt=untilDt
        )
        points_samples = await self._repo.sample_points(
            strategyId=strat_id, sinceDt=sinceDt, untilDt=untilDt
        )

        breakdown = _status_breakdown(status_raw)
        if breakdown.total:
            success_rate = breakdown.ok / breakdown.total
            error_rate = (
                breakdown.error + breakdown.timeout + breakdown.limit
            ) / breakdown.total
        else:
            success_rate = 0.0
            error_rate = 0.0

        sorted_durations = sorted(duration_samples)
        percentiles = DurationPercentiles(
            avgMs=summary["durationAvgMs"],
            p50Ms=_percentile(sorted_durations, 0.50),
            p95Ms=_percentile(sorted_durations, 0.95),
            p99Ms=_percentile(sorted_durations, 0.99),
            maxMs=summary["durationMaxMs"],
            sampleSize=len(sorted_durations),
        )

        return StrategyMetricsResponse(
            strategyId=strat_id,
            name=strategy.name,
            version=strategy.version,
            status=strategy.status,
            windowFrom=sinceDt,
            windowUntil=untilDt,
            statusBreakdown=breakdown,
            successRate=success_rate,
            errorRate=error_rate,
            duration=percentiles,
            durationHistogram=_duration_histogram(duration_samples),
            topErrors=[
                ErrorCount(code=e["code"], count=e["count"]) for e in top_errors
            ],
            topCases=[
                CaseCount(caseName=c["caseName"], count=c["count"]) for c in top_cases
            ],
            pointsHistogram=_points_histogram(points_samples),
            pointsSum=summary["pointsSum"],
            nodesAvg=summary["nodesAvg"],
            nodesMax=summary["nodesMax"],
        )
