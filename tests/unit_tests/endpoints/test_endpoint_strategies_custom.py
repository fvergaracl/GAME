"""
Endpoint-level tests for /v1/strategies/custom.

We call the endpoint functions directly with mocked services and auth
contexts, mirroring the existing pattern in
``test_endpoint_strategy.py``. The point is to lock down the tenant
resolution, the admin gates, and the audit logging on success/failure
paths — the underlying service is exercised in
``test_strategy_definition_service``.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.endpoints import strategies_custom as endpoint
from app.core.config import configs
from app.core.exceptions import ForbiddenError
from app.middlewares.auth_context import AuditLogger, AuthContext
from app.model.strategy_definition import StrategyDefinitionType
from app.schema.strategy_definition_schema import (
    StrategyDefinitionCreate,
    StrategyDefinitionRead,
    StrategyDefinitionUpdate,
)


def _auth(*, api_key=None, oauth_user_id=None, is_admin=False) -> AuthContext:
    return AuthContext(
        api_key=api_key,
        oauth_user_id=oauth_user_id,
        is_admin=is_admin,
        token_data={"sub": oauth_user_id} if oauth_user_id else None,
    )


def _audit(auth: AuthContext) -> AuditLogger:
    return AuditLogger("strategies_custom", MagicMock(), auth)


def _read_stub(**overrides) -> StrategyDefinitionRead:
    base = {
        "id": "row-1",
        "realmId": "realm-a",
        "name": "demo",
        "description": None,
        "type": "DSL_FULL",
        "parentStrategyId": None,
        "astJson": None,
        "blocklyXml": None,
        "version": 1,
        "status": "DRAFT",
        "createdBy": None,
        "created_at": None,
        "updated_at": None,
        "publishedAt": None,
        "experimentTag": None,
    }
    base.update(overrides)
    return StrategyDefinitionRead(**base)


# ---------------------------------------------------------------- realm


def test_resolve_realm_id_prefers_api_key_over_keycloak_realm():
    auth = _auth(api_key="api-key-xyz", oauth_user_id="user-1")
    assert endpoint._resolve_realm_id(auth) == "api-key-xyz"


def test_resolve_realm_id_falls_back_to_configured_keycloak_realm():
    auth = _auth(oauth_user_id="user-1")
    assert endpoint._resolve_realm_id(auth) == configs.KEYCLOAK_REALM


def test_resolve_realm_id_refuses_anonymous_caller():
    with pytest.raises(ForbiddenError):
        endpoint._resolve_realm_id(_auth())


# ---------------------------------------------------------------- create


@pytest.mark.asyncio
async def test_create_passes_resolved_realm_to_service():
    service = MagicMock()
    service.create = AsyncMock(return_value=_read_stub())
    payload = StrategyDefinitionCreate(
        name="demo", type=StrategyDefinitionType.DSL_FULL
    )
    auth = _auth(api_key="api-key-xyz", oauth_user_id="user-1")

    with patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ):
        result = await endpoint.create_custom_strategy(
            payload=payload,
            auth=auth,
            service=service,
            audit=_audit(auth),
        )

    service.create.assert_awaited_once()
    call_kwargs = service.create.await_args.kwargs
    assert call_kwargs["realmId"] == "api-key-xyz"
    assert call_kwargs["createdBy"] == "user-1"
    assert call_kwargs["apiKey_used"] == "api-key-xyz"
    assert result.name == "demo"


@pytest.mark.asyncio
async def test_create_logs_error_when_service_fails():
    service = MagicMock()
    service.create = AsyncMock(side_effect=RuntimeError("boom"))
    payload = StrategyDefinitionCreate(
        name="demo", type=StrategyDefinitionType.DSL_FULL
    )
    auth = _auth(api_key="api-key-xyz")

    with patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ) as mock_add_log:
        with pytest.raises(RuntimeError, match="boom"):
            await endpoint.create_custom_strategy(
                payload=payload,
                auth=auth,
                service=service,
                audit=_audit(auth),
            )

    # One INFO for the attempt + one ERROR for the failure.
    assert mock_add_log.await_count == 2


# ---------------------------------------------------------------- list


@pytest.mark.asyncio
async def test_list_scopes_query_to_caller_realm():
    service = MagicMock()
    service.list_strategies = AsyncMock(return_value=[_read_stub()])

    result = await endpoint.list_custom_strategies(
        status_filter=None,
        type_filter=None,
        limit=100,
        auth=_auth(api_key="api-key-xyz"),
        service=service,
    )

    service.list_strategies.assert_awaited_once_with(
        realmId="api-key-xyz",
        status=None,
        type=None,
        limit=100,
    )
    assert len(result) == 1


# ---------------------------------------------------------------- publish / archive


@pytest.mark.asyncio
async def test_publish_requires_admin_gate_to_have_passed():
    service = MagicMock()
    service.publish = AsyncMock(return_value=_read_stub(status="PUBLISHED"))
    auth = _auth(oauth_user_id="admin-1", is_admin=True)

    with patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ):
        result = await endpoint.publish_custom_strategy(
            id="row-1",
            auth=auth,
            service=service,
            audit=_audit(auth),
        )

    service.publish.assert_awaited_once_with(
        id="row-1", realmId=configs.KEYCLOAK_REALM
    )
    assert result.status == "PUBLISHED"


@pytest.mark.asyncio
async def test_require_admin_dependency_rejects_non_admin():
    with pytest.raises(ForbiddenError):
        await endpoint.require_admin(
            _auth(oauth_user_id="user-1", is_admin=False)
        )


@pytest.mark.asyncio
async def test_archive_calls_service_with_tenant_scope():
    service = MagicMock()
    service.archive = AsyncMock(return_value=_read_stub(status="ARCHIVED"))
    auth = _auth(api_key="api-key-xyz", is_admin=True)

    with patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ):
        result = await endpoint.archive_custom_strategy(
            id="row-1",
            auth=auth,
            service=service,
            audit=_audit(auth),
        )

    service.archive.assert_awaited_once_with(
        id="row-1", realmId="api-key-xyz"
    )
    assert result.status == "ARCHIVED"


# ---------------------------------------------------------------- update


@pytest.mark.asyncio
async def test_update_passes_payload_through():
    service = MagicMock()
    service.update = AsyncMock(return_value=_read_stub(description="new"))
    payload = StrategyDefinitionUpdate(description="new")
    auth = _auth(api_key="api-key-xyz")

    with patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ):
        result = await endpoint.update_custom_strategy(
            id="row-1",
            payload=payload,
            auth=auth,
            service=service,
            audit=_audit(auth),
        )

    service.update.assert_awaited_once()
    call_kwargs = service.update.await_args.kwargs
    assert call_kwargs["id"] == "row-1"
    assert call_kwargs["payload"].description == "new"
    assert call_kwargs["realmId"] == "api-key-xyz"
    assert result.description == "new"


# ---------------------------------------------------------------- parent check
#
# Sprint 7: when type=DSL_EXTEND, the endpoint must verify the
# referenced parentStrategyId exists in the built-in registry BEFORE
# the row gets persisted. Without this check, designers could persist
# DSL_EXTEND rows that crash at execution time with a confusing
# NotFoundError deep in StrategyService.get_strategy_instance.


from app.core.exceptions import NotFoundError  # noqa: E402


@pytest.mark.asyncio
async def test_create_with_dsl_extend_rejects_unknown_parent():
    """A DSL_EXTEND payload whose parentStrategyId is not in the
    registry must 404 before the service.create call — proves the
    new ``_ensure_parent_strategy_exists`` guard is wired correctly."""
    service = MagicMock()
    service.create = AsyncMock()
    strategy_service = MagicMock()
    strategy_service.get_strategy_by_id.side_effect = NotFoundError(
        detail="Strategy not found with id: ghost"
    )

    payload = StrategyDefinitionCreate(
        name="extend_ghost",
        type=StrategyDefinitionType.DSL_EXTEND,
        parentStrategyId="ghost",
    )
    auth = _auth(api_key="api-key-xyz")

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        with pytest.raises(NotFoundError, match="ghost"):
            await endpoint.create_custom_strategy(
                payload=payload,
                auth=auth,
                service=service,
                strategy_service=strategy_service,
                audit=_audit(auth),
            )

    strategy_service.get_strategy_by_id.assert_called_once_with("ghost")
    # The persistence layer is never reached.
    service.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_with_dsl_extend_passes_when_parent_exists():
    """Happy path: a real built-in id allows the DSL_EXTEND row to
    be persisted normally."""
    service = MagicMock()
    service.create = AsyncMock(return_value=_read_stub(type="DSL_EXTEND"))
    strategy_service = MagicMock()
    strategy_service.get_strategy_by_id.return_value = {
        "id": "default", "name": "Default",
    }

    payload = StrategyDefinitionCreate(
        name="extend_default",
        type=StrategyDefinitionType.DSL_EXTEND,
        parentStrategyId="default",
    )
    auth = _auth(api_key="api-key-xyz")

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        result = await endpoint.create_custom_strategy(
            payload=payload,
            auth=auth,
            service=service,
            strategy_service=strategy_service,
            audit=_audit(auth),
        )

    strategy_service.get_strategy_by_id.assert_called_once_with("default")
    service.create.assert_awaited_once()
    assert result.type == "DSL_EXTEND"


@pytest.mark.asyncio
async def test_create_with_dsl_full_skips_parent_check():
    """For DSL_FULL payloads the parent check is a no-op — confirms
    the early-return guard in _ensure_parent_strategy_exists."""
    service = MagicMock()
    service.create = AsyncMock(return_value=_read_stub())
    strategy_service = MagicMock()
    # If this ever runs, ``get_strategy_by_id`` would explode the test.
    strategy_service.get_strategy_by_id.side_effect = AssertionError(
        "Parent check should not run for DSL_FULL"
    )

    payload = StrategyDefinitionCreate(
        name="full_only", type=StrategyDefinitionType.DSL_FULL,
    )
    auth = _auth(api_key="api-key-xyz")

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        await endpoint.create_custom_strategy(
            payload=payload,
            auth=auth,
            service=service,
            strategy_service=strategy_service,
            audit=_audit(auth),
        )

    strategy_service.get_strategy_by_id.assert_not_called()
    service.create.assert_awaited_once()
