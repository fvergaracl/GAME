"""
Prometheus metrics for the DSL strategy engine (Sprint 11).

Three metrics, scraped by the standard ``/metrics`` endpoint exposed by
``prometheus_fastapi_instrumentator`` (already in pyproject.toml):

* ``dsl_execution_duration_seconds`` -- histogram of wall-clock time
  per ``DslStrategy.calculate_points`` call. The bucket layout zooms
  in on the SLO at 250ms so the p99 alert rule is computed off a
  realistic bucket boundary (and not extrapolated between 0.1 and 1.0
  buckets, which would mis-fire).
* ``dsl_execution_nodes_total`` -- counter incremented by the number
  of AST nodes the interpreter visited. Lets ops correlate cost
  with rule complexity, separately from time.
* ``dsl_execution_errors_total`` -- per-realm error counter. Labels
  carry the error code (``DSL_TIMEOUT``, ``DSL_ARITH_DIV_BY_ZERO``,
  etc.) so a noisy realm + code combination jumps out in the
  dashboard.

Labels are intentionally minimal:

* ``realmId`` lets the on-call team page only the affected tenant.
  Cardinality is bounded by the number of realms (small).
* ``strategy_type`` (``DSL_FULL`` / ``DSL_EXTEND``) -- two values
  total, so we can split the latency dashboard.
* ``status`` (``ok`` / ``error`` / ``timeout`` / ``limit``) on the
  duration histogram so a healthy p99 isn't dragged down by long
  error paths.

We deliberately do *not* label by strategyId. Strategy UUIDs are
high-cardinality (one per realm × name × version) and would explode
Prometheus' index. The persisted ``StrategyExecutionLog`` covers the
per-strategy view; metrics stay aggregate.

The histogram buckets matter for the alert rule. ``histogram_quantile``
linearly interpolates between bucket boundaries, so a bucket at 0.25
is required for an accurate p99 alert at 250ms.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

DSL_LATENCY_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.15,
    0.2,
    0.25,
    0.3,
    0.4,
    0.5,
    0.75,
    1.0,
    2.5,
    5.0,
)

dsl_execution_duration_seconds = Histogram(
    "dsl_execution_duration_seconds",
    "Wall-clock duration of a DslStrategy.calculate_points run.",
    labelnames=("realm", "strategy_type", "status"),
    buckets=DSL_LATENCY_BUCKETS,
)

dsl_execution_nodes_total = Counter(
    "dsl_execution_nodes_total",
    "Total AST nodes visited by the DSL interpreter.",
    labelnames=("realm", "strategy_type"),
)

dsl_execution_errors_total = Counter(
    "dsl_execution_errors_total",
    "DSL strategy executions that ended in error.",
    labelnames=("realm", "strategy_type", "code"),
)

# Sprint 13: persistence is now drained off the scoring hot-path by a
# background worker fed from a bounded queue. When the queue is full
# (a slow/unavailable DB causing the worker to fall behind) the observer
# drops the audit row rather than applying backpressure to scoring. This
# counter makes those drops visible so ops can alert on a saturated sink
# instead of silently losing execution logs.
dsl_execution_log_dropped_total = Counter(
    "dsl_execution_log_dropped_total",
    "StrategyExecutionLog rows dropped because the persistence queue "
    "was full (scoring is never blocked on the audit log).",
    labelnames=("realm", "strategy_type"),
)


def _label(value: str | None) -> str:
    """
    Coerce ``None`` to ``"unknown"`` so Prometheus -- which rejects
    None as a label value -- doesn't raise mid-scoring. ``unknown``
    is rare in practice (only the legacy unauth path with no API key
    + no oauth user); aggregating it under one bucket is fine.
    """
    return value if value else "unknown"


def observe(
    *,
    realm: str | None,
    strategy_type: str,
    status: str,
    duration_seconds: float,
    nodes_executed: int,
    error_code: str | None = None,
) -> None:
    """
    Single emit point so the observer in ``DslStrategy`` doesn't
    duplicate the label-coercion logic.
    """
    realm_label = _label(realm)
    type_label = _label(strategy_type)
    dsl_execution_duration_seconds.labels(
        realm=realm_label,
        strategy_type=type_label,
        status=status,
    ).observe(duration_seconds)
    dsl_execution_nodes_total.labels(
        realm=realm_label,
        strategy_type=type_label,
    ).inc(nodes_executed)
    if status != "ok":
        dsl_execution_errors_total.labels(
            realm=realm_label,
            strategy_type=type_label,
            code=_label(error_code),
        ).inc()


def observe_log_dropped(
    *,
    realm: str | None,
    strategy_type: str,
) -> None:
    """
    Record that one StrategyExecutionLog row was dropped because the
    background persistence queue was full. Kept separate from
    :func:`observe` so the hot path only touches it on the rare drop.
    """
    dsl_execution_log_dropped_total.labels(
        realm=_label(realm),
        strategy_type=_label(strategy_type),
    ).inc()
