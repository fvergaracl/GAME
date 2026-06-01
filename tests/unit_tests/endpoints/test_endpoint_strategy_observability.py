"""
Sprint 10 — endpoint-level tests for /v1/strategies/custom/{id}/metrics
and /v1/strategies/custom/compare.

Mirrors the calling pattern in ``test_endpoint_strategies_custom.py``:
we call the endpoint functions directly with mocked services and a
faked AuthContext to pin tenant scoping + auth gating without standing
up a TestClient.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.endpoints import strategy_observability as endpoint
from app.core.config import configs
from app.core.exceptions import ForbiddenError
from app.middlewares.auth_context import AuthContext
from app.schema.strategy_observability_schema import (
    DurationPercentiles,
    MetricsDelta,
    StatusBreakdown,
    StrategyComparisonResponse,
    StrategyMetricsResponse,
)


def _auth(*, api_key=None, oauth_user_id=None, is_admin=False) -> AuthContext:
    return AuthContext(
        api_key=api_key,
        oauth_user_id=oauth_user_id,
        is_admin=is_admin,
        token_data={"sub": oauth_user_id} if oauth_user_id else None,
    )


def _metrics_stub(strategy_id: str = "s1") -> StrategyMetricsResponse:
    return StrategyMetricsResponse(
        strategyId=strategy_id,
        name="demo",
        version=1,
        status="PUBLISHED",
        statusBreakdown=StatusBreakdown(ok=10, total=10),
        successRate=1.0,
        errorRate=0.0,
        duration=DurationPercentiles(),
    )


@pytest.mark.asyncio
async def test_metrics_passes_resolved_realm_and_window_to_service():
    service = MagicMock()
    service.get_metrics = AsyncMock(return_value=_metrics_stub())
    auth = _auth(api_key="api-key-xyz")

    result = await endpoint.get_strategy_metrics(
        id="s1",
        sinceDt=None,
        untilDt=None,
        auth=auth,
        service=service,
    )

    service.get_metrics.assert_awaited_once_with(
        id="s1", realmId="api-key-xyz", sinceDt=None, untilDt=None,
    )
    assert result.strategyId == "s1"


@pytest.mark.asyncio
async def test_metrics_falls_back_to_keycloak_realm_for_oauth_admin():
    # Mirrors the tenant convention from strategies_custom: API-key
    # callers scope to their key value, Keycloak admins to the
    # configured KEYCLOAK_REALM.
    service = MagicMock()
    service.get_metrics = AsyncMock(return_value=_metrics_stub())
    auth = _auth(oauth_user_id="admin-1", is_admin=True)

    await endpoint.get_strategy_metrics(
        id="s1",
        sinceDt=None,
        untilDt=None,
        auth=auth,
        service=service,
    )
    service.get_metrics.assert_awaited_once_with(
        id="s1",
        realmId=configs.KEYCLOAK_REALM,
        sinceDt=None,
        untilDt=None,
    )


@pytest.mark.asyncio
async def test_metrics_refuses_anonymous_caller():
    # The shared ``_resolve_realm_id`` helper refuses an anonymous
    # caller; the endpoint must surface that 403 before the service is
    # ever consulted.
    service = MagicMock()
    service.get_metrics = AsyncMock()
    auth = _auth()

    with pytest.raises(ForbiddenError):
        await endpoint.get_strategy_metrics(
            id="s1",
            sinceDt=None,
            untilDt=None,
            auth=auth,
            service=service,
        )
    service.get_metrics.assert_not_called()


@pytest.mark.asyncio
async def test_compare_passes_both_ids_and_realm_through():
    service = MagicMock()
    service.compare = AsyncMock(
        return_value=StrategyComparisonResponse(
            a=_metrics_stub("a"),
            b=_metrics_stub("b"),
            delta=MetricsDelta(),
        )
    )
    auth = _auth(api_key="api-key-xyz")

    result = await endpoint.compare_strategies(
        idA="a",
        idB="b",
        sinceDt=None,
        untilDt=None,
        auth=auth,
        service=service,
    )

    service.compare.assert_awaited_once_with(
        idA="a",
        idB="b",
        realmId="api-key-xyz",
        sinceDt=None,
        untilDt=None,
    )
    assert result.a.strategyId == "a"
    assert result.b.strategyId == "b"
