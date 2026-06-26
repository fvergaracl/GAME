"""
Observability endpoints for custom strategies.

Exposes the data the backend already collects (via
:class:`DslExecutionObserver` writing into ``strategyexecutionlog``)
as a single JSON payload the dashboard renders into a metrics card,
plus an A/B comparison endpoint that runs the same aggregation against
two strategy ids and returns deltas server-side.

These routes live in their own router (and not piggybacked under
``strategies_custom``) so the metrics surface can evolve independently
of the CRUD surface, and a future per-strategy access policy can gate
them separately. Tenant scoping is reused verbatim from
:mod:`strategies_custom`.
"""

from datetime import datetime
from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.api.v1.endpoints.strategies_custom import (
    _resolve_realm_id,
    require_authenticated,
)
from app.core.container import Container
from app.middlewares.auth_context import AuthContext
from app.schema.strategy_observability_schema import (
    StrategyComparisonResponse,
    StrategyMetricsResponse,
)
from app.services.strategy_observability_service import StrategyObservabilityService

router = APIRouter(
    prefix="/strategies/custom",
    tags=["strategies", "observability"],
)


@router.get(
    "/{id}/metrics",
    response_model=StrategyMetricsResponse,
    summary="Observability metrics for a custom strategy",
)
@inject
async def get_strategy_metrics(
    id: str,
    sinceDt: Optional[datetime] = Query(
        default=None,
        alias="since",
        description=(
            "ISO-8601 lower bound. Filters the aggregations by "
            "``created_at``. Omit for an all-time view."
        ),
    ),
    untilDt: Optional[datetime] = Query(
        default=None,
        alias="until",
        description="ISO-8601 upper bound (inclusive).",
    ),
    auth: AuthContext = Depends(require_authenticated),
    service: StrategyObservabilityService = Depends(
        Provide[Container.strategy_observability_service]
    ),
) -> StrategyMetricsResponse:
    """
    Aggregate metrics rendered by the dashboard:
      * status mix (ok / error / timeout / limit)
      * latency percentiles + duration histogram
      * top error codes (when failures occurred)
      * case-name breakdown (which rule branch fired)
      * points distribution + nodes-executed summary

    Tenant-scoped via the underlying ``get_strategy`` call - 404s on
    cross-realm probes before the metrics query runs.
    """
    realm = _resolve_realm_id(auth)
    return await service.get_metrics(
        id=id,
        realmId=realm,
        sinceDt=sinceDt,
        untilDt=untilDt,
    )


@router.get(
    "/compare",
    response_model=StrategyComparisonResponse,
    summary="Side-by-side A/B comparison of two strategies",
)
@inject
async def compare_strategies(
    idA: str = Query(
        ...,
        alias="a",
        description="Strategy A - id of the baseline.",
    ),
    idB: str = Query(
        ...,
        alias="b",
        description="Strategy B - id of the variant being compared.",
    ),
    sinceDt: Optional[datetime] = Query(
        default=None,
        alias="since",
        description="ISO-8601 lower bound for the window.",
    ),
    untilDt: Optional[datetime] = Query(
        default=None,
        alias="until",
        description="ISO-8601 upper bound for the window (inclusive).",
    ),
    auth: AuthContext = Depends(require_authenticated),
    service: StrategyObservabilityService = Depends(
        Provide[Container.strategy_observability_service]
    ),
) -> StrategyComparisonResponse:
    """
    Run the same per-strategy aggregation against ``a`` and ``b`` and
    return both snapshots plus deltas (B - A). Useful for the README's
    static vs adaptive / baseline vs experimental comparisons without
    leaving the dashboard.
    """
    realm = _resolve_realm_id(auth)
    return await service.compare(
        idA=idA,
        idB=idB,
        realmId=realm,
        sinceDt=sinceDt,
        untilDt=untilDt,
    )
