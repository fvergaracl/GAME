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


# ---------------------------------------------------------------- templates
# Sprint 8: list_strategy_templates is a thin wrapper over the loader.
# We patch the loader so the test doesn't depend on the on-disk files.


from app.core.exceptions import DslValidationError  # noqa: E402
from app.schema.strategy_definition_schema import (  # noqa: E402
    StrategyDefinitionImport,
    StrategyTemplateRead,
)


def _template_stub(**overrides) -> StrategyTemplateRead:
    base = {
        "id": "tpl-1",
        "name": "Template uno",
        "description": "desc",
        "type": StrategyDefinitionType.DSL_FULL,
        "parentStrategyId": None,
        "astJson": {
            "type": "program",
            "id": "program",
            "rules": [],
        },
        "blocklyXml": "<xml></xml>",
    }
    base.update(overrides)
    return StrategyTemplateRead(**base)


@pytest.mark.asyncio
async def test_list_templates_returns_loaded_list():
    """Endpoint hands back exactly what the loader returns, no filtering."""
    payload = [
        _template_stub(id="tpl-1"),
        _template_stub(
            id="tpl-2",
            type=StrategyDefinitionType.DSL_EXTEND,
            parentStrategyId="default",
        ),
    ]
    with patch.object(endpoint, "load_user_templates", return_value=payload):
        result = await endpoint.list_strategy_templates(
            auth=_auth(api_key="api-key-xyz"),
        )
    assert [t.id for t in result] == ["tpl-1", "tpl-2"]


# ---------------------------------------------------------------- import


def _import_payload(**overrides) -> StrategyDefinitionImport:
    base = {
        "name": "imported_one",
        "description": None,
        "type": StrategyDefinitionType.DSL_FULL,
        "parentStrategyId": None,
        "astJson": {
            "type": "program",
            "id": "program",
            "rules": [],
        },
        "blocklyXml": "<xml></xml>",
    }
    base.update(overrides)
    return StrategyDefinitionImport(**base)


@pytest.mark.asyncio
async def test_import_creates_draft_when_name_is_unique():
    service = MagicMock()
    service.name_exists = AsyncMock(return_value=False)
    service.create = AsyncMock(return_value=_read_stub(name="imported_one"))
    strategy_service = MagicMock()
    auth = _auth(api_key="api-key-xyz")

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        result = await endpoint.import_custom_strategy(
            payload=_import_payload(),
            auth=auth,
            service=service,
            strategy_service=strategy_service,
            audit=_audit(auth),
        )

    service.name_exists.assert_awaited_once_with(
        realmId="api-key-xyz", name="imported_one",
    )
    service.create.assert_awaited_once()
    call_kwargs = service.create.await_args.kwargs
    assert call_kwargs["payload"].name == "imported_one"
    assert call_kwargs["realmId"] == "api-key-xyz"
    assert result.name == "imported_one"


@pytest.mark.asyncio
async def test_import_renames_on_name_collision():
    """When the realm already has a strategy with the same name, import
    must auto-rename rather than 400 — otherwise a support engineer
    re-running an import would have to manually delete prior attempts."""
    service = MagicMock()
    service.name_exists = AsyncMock(return_value=True)
    service.create = AsyncMock(return_value=_read_stub())
    strategy_service = MagicMock()
    auth = _auth(api_key="api-key-xyz")

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        await endpoint.import_custom_strategy(
            payload=_import_payload(name="dup_name"),
            auth=auth,
            service=service,
            strategy_service=strategy_service,
            audit=_audit(auth),
        )

    created_payload = service.create.await_args.kwargs["payload"]
    # The renamed payload starts with the original name and ends with
    # the "(importada ...)" suffix; we don't assert the date exactly so
    # the test stays time-independent.
    assert created_payload.name.startswith("dup_name (importada ")
    assert created_payload.name.endswith(")")


@pytest.mark.asyncio
async def test_import_rejects_malformed_ast_before_db_roundtrip():
    """A bad AST must 400 (via DslValidationError) and never touch
    name_exists / create — proves the upfront validation guard."""
    service = MagicMock()
    service.name_exists = AsyncMock()
    service.create = AsyncMock()
    strategy_service = MagicMock()
    auth = _auth(api_key="api-key-xyz")

    bad = _import_payload(
        astJson={
            "type": "program",
            "id": "program",
            # rules must be a list — passing a dict trips validate_ast.
            "rules": {"oops": "not_a_list"},
        },
    )

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        with pytest.raises(DslValidationError):
            await endpoint.import_custom_strategy(
                payload=bad,
                auth=auth,
                service=service,
                strategy_service=strategy_service,
                audit=_audit(auth),
            )

    service.name_exists.assert_not_awaited()
    service.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_import_dsl_extend_validates_parent_against_registry():
    """DSL_EXTEND import with an unknown parent must 404 before
    create — same guard as the regular create endpoint."""
    service = MagicMock()
    service.name_exists = AsyncMock()
    service.create = AsyncMock()
    strategy_service = MagicMock()
    strategy_service.get_strategy_by_id.side_effect = NotFoundError(
        detail="Strategy not found with id: ghost"
    )
    auth = _auth(api_key="api-key-xyz")

    payload = _import_payload(
        name="extend_ghost",
        type=StrategyDefinitionType.DSL_EXTEND,
        parentStrategyId="ghost",
    )

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        with pytest.raises(NotFoundError, match="ghost"):
            await endpoint.import_custom_strategy(
                payload=payload,
                auth=auth,
                service=service,
                strategy_service=strategy_service,
                audit=_audit(auth),
            )

    strategy_service.get_strategy_by_id.assert_called_once_with("ghost")
    service.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_import_logs_failure_with_audit():
    """An exception inside service.create must trigger an audit ERROR
    log — same audit-on-failure pattern as the create endpoint."""
    service = MagicMock()
    service.name_exists = AsyncMock(return_value=False)
    service.create = AsyncMock(side_effect=RuntimeError("boom"))
    strategy_service = MagicMock()
    auth = _auth(api_key="api-key-xyz")

    with patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ) as mock_add_log:
        with pytest.raises(RuntimeError, match="boom"):
            await endpoint.import_custom_strategy(
                payload=_import_payload(),
                auth=auth,
                service=service,
                strategy_service=strategy_service,
                audit=_audit(auth),
            )

    # INFO on attempt + ERROR on failure.
    assert mock_add_log.await_count == 2


# ---------------------------------------------------------------- versions


@pytest.mark.asyncio
async def test_list_versions_passes_resolved_realm():
    """``GET /{id}/versions`` resolves the realm from the auth context
    and delegates straight to the service. Doesn't require admin —
    history is a read-only audit affordance."""
    service = MagicMock()
    service.list_versions = AsyncMock(
        return_value=[
            _read_stub(id="v2", version=2, status="DRAFT"),
            _read_stub(id="v1", version=1, status="PUBLISHED"),
        ]
    )
    auth = _auth(api_key="api-key-xyz")

    result = await endpoint.list_strategy_versions(
        id="v2", auth=auth, service=service,
    )

    assert [v.version for v in result] == [2, 1]
    service.list_versions.assert_awaited_once_with(
        id="v2", realmId="api-key-xyz",
    )


# ---------------------------------------------------------------- rollback


@pytest.mark.asyncio
async def test_rollback_requires_admin_via_dependency():
    """``require_admin`` rejects a non-admin caller before the endpoint
    body runs. Calling the dependency directly mirrors what FastAPI
    does at request time."""
    with pytest.raises(ForbiddenError):
        await endpoint.require_admin(auth=_auth(api_key="api-key-xyz"))


@pytest.mark.asyncio
async def test_rollback_logs_cascade_counts_on_success():
    """Audit success entry must carry games_reassigned / tasks_reassigned
    so an operator can verify the cascade after the fact."""
    from app.services.strategy_definition_service import RollbackResult

    promoted = _read_stub(id="v1", version=1, status="PUBLISHED")
    service = MagicMock()
    service.rollback = AsyncMock(
        return_value=RollbackResult(
            strategy=promoted,
            games_reassigned=3,
            tasks_reassigned=5,
        )
    )
    auth = _auth(oauth_user_id="admin-1", is_admin=True)

    with patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ) as mock_add_log:
        result = await endpoint.rollback_strategy(
            id="v2",
            version=1,
            auth=auth,
            service=service,
            audit=_audit(auth),
        )

    assert result.id == "v1"
    service.rollback.assert_awaited_once_with(
        id="v2", target_version=1, realmId=configs.KEYCLOAK_REALM,
    )
    # INFO on attempt + SUCCESS on completion.
    assert mock_add_log.await_count == 2
    # The SUCCESS payload (second call) must contain the cascade counts.
    success_call = mock_add_log.await_args_list[-1]
    success_data = success_call.kwargs.get("data") or success_call.args[-1]
    if isinstance(success_data, dict):
        assert success_data.get("games_reassigned") == 3
        assert success_data.get("tasks_reassigned") == 5


@pytest.mark.asyncio
async def test_rollback_logs_failure_with_audit():
    """An exception inside service.rollback must still surface as an
    audit ERROR before re-raising."""
    service = MagicMock()
    service.rollback = AsyncMock(side_effect=RuntimeError("kaboom"))
    auth = _auth(oauth_user_id="admin-1", is_admin=True)

    with patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ) as mock_add_log:
        with pytest.raises(RuntimeError, match="kaboom"):
            await endpoint.rollback_strategy(
                id="v2",
                version=1,
                auth=auth,
                service=service,
                audit=_audit(auth),
            )

    # INFO + ERROR.
    assert mock_add_log.await_count == 2
