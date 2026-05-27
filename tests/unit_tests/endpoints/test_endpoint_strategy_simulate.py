"""
Endpoint tests for the /v1/strategies/custom/{id}/simulate route.

Mirrors the pattern used in test_endpoint_strategies_custom.py: call the
endpoint function directly with a mocked simulation service and assert
the realm scoping + audit behaviour, since the service is exercised
exhaustively in its own test module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.endpoints import strategies_custom as endpoint
from app.core.config import configs
from app.core.exceptions import DslTimeoutError, DslValidationError, ForbiddenError
from app.middlewares.auth_context import AuditLogger, AuthContext
from app.schema.dsl_schema import SimulationRequest, SimulationResponse


def _auth(*, api_key=None, oauth_user_id=None, is_admin=False) -> AuthContext:
    return AuthContext(
        api_key=api_key,
        oauth_user_id=oauth_user_id,
        is_admin=is_admin,
        token_data={"sub": oauth_user_id} if oauth_user_id else None,
    )


def _audit(auth: AuthContext) -> AuditLogger:
    return AuditLogger("strategies_custom", MagicMock(), auth)


def _request():
    return SimulationRequest(
        externalGameId="g",
        externalTaskId="t",
        externalUserId="u",
    )


def _stub_response():
    return SimulationResponse(
        points=3.0,
        caseName="BasicEngagement",
        callbackData={},
        executionTrace=[],
    )


@pytest.mark.asyncio
async def test_simulate_passes_resolved_realm_to_service():
    service = MagicMock()
    service.simulate = AsyncMock(return_value=_stub_response())
    auth = _auth(api_key="api-key-xyz", oauth_user_id="user-1")

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        result = await endpoint.simulate_custom_strategy(
            id="row-1",
            payload=_request(),
            auth=auth,
            service=service,
            audit=_audit(auth),
        )

    service.simulate.assert_awaited_once()
    call_kwargs = service.simulate.await_args.kwargs
    assert call_kwargs["id"] == "row-1"
    assert call_kwargs["realmId"] == "api-key-xyz"
    assert call_kwargs["request"].externalUserId == "u"
    assert result.caseName == "BasicEngagement"


@pytest.mark.asyncio
async def test_simulate_falls_back_to_keycloak_realm_for_oauth_caller():
    service = MagicMock()
    service.simulate = AsyncMock(return_value=_stub_response())
    auth = _auth(oauth_user_id="admin-1")

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        await endpoint.simulate_custom_strategy(
            id="row-1",
            payload=_request(),
            auth=auth,
            service=service,
            audit=_audit(auth),
        )

    assert service.simulate.await_args.kwargs["realmId"] == configs.KEYCLOAK_REALM


@pytest.mark.asyncio
async def test_simulate_rejects_anonymous_caller():
    """The require_authenticated dependency is the gate; assert it 403s."""
    with pytest.raises(ForbiddenError):
        await endpoint.require_authenticated(_auth())


@pytest.mark.asyncio
async def test_simulate_logs_error_when_validation_fails():
    service = MagicMock()
    service.simulate = AsyncMock(
        side_effect=DslValidationError(detail="bad ast")
    )
    auth = _auth(api_key="api-key-xyz")

    with patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ) as mock_add_log:
        with pytest.raises(DslValidationError):
            await endpoint.simulate_custom_strategy(
                id="row-1",
                payload=_request(),
                auth=auth,
                service=service,
                audit=_audit(auth),
            )

    # Info entry on attempt + error entry on failure.
    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_simulate_propagates_timeout_as_dsl_timeout_error():
    service = MagicMock()
    service.simulate = AsyncMock(side_effect=DslTimeoutError(detail="too slow"))
    auth = _auth(api_key="api-key-xyz")

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        with pytest.raises(DslTimeoutError):
            await endpoint.simulate_custom_strategy(
                id="row-1",
                payload=_request(),
                auth=auth,
                service=service,
                audit=_audit(auth),
            )
