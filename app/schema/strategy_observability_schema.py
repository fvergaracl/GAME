"""
Pydantic schemas for the observability endpoints.

The backend already collects every datapoint via ``DslExecutionObserver``
(metrics + sampled persistence into ``strategyexecutionlog``). This
module shapes those rows into a response the dashboard can render in
one fetch, plus an A/B comparison payload built by running the same
aggregation against two strategy ids and computing deltas server-side.

Why aggregations land here rather than just exposing raw rows:
  * The log is sampled - emitting per-event JSON would let the UI
    silently under-count, which defeats the point of an observability
    view ("the strategy looks fine, but actually it's timing out 30%
    of the time").
  * Percentiles, status mix and bucketed histograms each take a single
    pass through the data on the DB side; doing them client-side would
    multiply payload size by 100x for the same information.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StatusBreakdown(BaseModel):
    """Run counts grouped by terminal status."""

    ok: int = 0
    error: int = 0
    timeout: int = 0
    limit: int = 0
    other: int = 0
    total: int = 0


class ErrorCount(BaseModel):
    """One DSL_* error code and how often it fired."""

    code: str
    count: int


class CaseCount(BaseModel):
    """A ``case_name`` returned by the strategy and how often it fired.

    ``caseName`` is ``None`` when the strategy fell through every rule
    and returned its defaultPoints - that is the "default" bucket the
    dashboard renders separately.
    """

    caseName: Optional[str] = None
    count: int


class HistogramBucket(BaseModel):
    """One bucket of a fixed-edge histogram. ``upperBoundMs`` is
    inclusive; the last bucket is everything ≥ the previous edge."""

    label: str
    upperBound: Optional[float] = None
    count: int


class DurationPercentiles(BaseModel):
    """Latency percentiles computed in Python from a bounded sample."""

    avgMs: float = 0.0
    p50Ms: float = 0.0
    p95Ms: float = 0.0
    p99Ms: float = 0.0
    maxMs: float = 0.0
    sampleSize: int = 0


class StrategyMetricsResponse(BaseModel):
    """The full observability payload for a single strategy version.

    The dashboard renders 5 cards from this:
      * status mix (ok/error/timeout rates)
      * latency percentiles + duration histogram
      * top error codes
      * case-name breakdown
      * points distribution + nodes-executed summary

    ``windowFrom``/``windowUntil`` echo back the time window the
    aggregations were computed over so the UI can label the chart with
    the actual range (the caller may not have passed explicit bounds).
    """

    strategyId: str
    name: Optional[str] = None
    version: Optional[int] = None
    status: Optional[str] = None
    windowFrom: Optional[datetime] = None
    windowUntil: Optional[datetime] = None
    statusBreakdown: StatusBreakdown
    successRate: float = 0.0  # in [0, 1]
    errorRate: float = 0.0
    duration: DurationPercentiles
    durationHistogram: List[HistogramBucket] = Field(default_factory=list)
    topErrors: List[ErrorCount] = Field(default_factory=list)
    topCases: List[CaseCount] = Field(default_factory=list)
    pointsHistogram: List[HistogramBucket] = Field(default_factory=list)
    pointsSum: float = 0.0
    nodesAvg: float = 0.0
    nodesMax: int = 0

    model_config = ConfigDict(from_attributes=True)


class MetricsDelta(BaseModel):
    """Side-by-side deltas surfaced in the A/B view."""

    successRate: float = 0.0
    errorRate: float = 0.0
    p95Ms: float = 0.0
    avgMs: float = 0.0
    pointsAvg: float = 0.0


class StrategyComparisonResponse(BaseModel):
    """A/B comparison payload - two metric snapshots plus deltas.

    Deltas are ``B - A`` so a positive ``successRate`` delta means B is
    healthier, a positive ``p95Ms`` means B is slower. The UI surfaces
    both percentages and absolute numbers so a viewer can judge whether
    a 2% delta is meaningful (it is, if it's 2% of 100k runs).
    """

    a: StrategyMetricsResponse
    b: StrategyMetricsResponse
    delta: MetricsDelta
