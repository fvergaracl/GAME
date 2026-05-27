"""
CRUD endpoints for custom (DB-persisted) strategies — Sprint 3.

These endpoints are kept under a separate router (``/v1/strategies/custom``)
so the legacy ``/v1/strategies`` listing of built-ins keeps a clean schema
and existing integrations don't see new fields appear.

Tenant scoping:
  Every read/write is bound to a ``realmId`` resolved from the caller's
  auth context. API-key callers use the api key itself; Keycloak admins
  fall back to the configured ``KEYCLOAK_REALM``. The roadmap calls out
  that we should explicitly forbid an API key from reading another
  realm's strategies and we do exactly that here.
"""

from typing import List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from app.core.config import configs
from app.core.container import Container
from app.core.exceptions import ForbiddenError
from app.middlewares.auth_context import (
    AuditLogger,
    AuthContext,
    audit_log,
    get_auth_context,
)
from app.schema.dsl_schema import SimulationRequest, SimulationResponse
from app.schema.strategy_definition_schema import (
    StrategyDefinitionCreate,
    StrategyDefinitionRead,
    StrategyDefinitionUpdate,
)
from app.services.dsl_simulation_service import DslSimulationService
from app.services.strategy_definition_service import (
    StrategyDefinitionService,
)

router = APIRouter(
    prefix="/strategies/custom",
    tags=["strategies"],
)


def _resolve_realm_id(auth: AuthContext) -> str:
    """
    Convention used by Sprint 3:
      * API-key caller → its api key value is the tenant boundary.
      * OAuth admin    → the configured Keycloak realm is the boundary.

    Anything else → 403. We refuse to write to or read from a "null"
    tenant so a misconfigured caller can't poison the global namespace.
    """
    if auth.api_key:
        return auth.api_key
    if auth.oauth_user_id:
        return configs.KEYCLOAK_REALM
    raise ForbiddenError(
        detail=(
            "Custom strategy endpoints require an authenticated caller "
            "(API key or Keycloak admin)."
        )
    )


async def require_authenticated(
    auth: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    """
    Lightweight gate: reject anonymous callers. We don't gate by the
    AdministratorGAME role here because the Sprint 3 plan calls for a
    finer-grained policy (``StrategyAuthor`` edits drafts, only admins
    publish). Until that role exists in Keycloak the publish/archive
    endpoints additionally enforce the admin check below.
    """
    if not auth.api_key and not auth.oauth_user_id:
        raise ForbiddenError(
            detail=(
                "Custom strategy endpoints require an authenticated "
                "caller (API key or Keycloak admin)."
            )
        )
    return auth


async def require_admin(
    auth: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    """Strict admin gate for publish/archive operations."""
    if not auth.is_admin:
        raise ForbiddenError(
            detail=(
                "Publishing or archiving a strategy requires an "
                "authenticated administrator (role: AdministratorGAME)."
            )
        )
    return auth


@router.post(
    "",
    response_model=StrategyDefinitionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom strategy draft",
)
@inject
async def create_custom_strategy(
    payload: StrategyDefinitionCreate,
    auth: AuthContext = Depends(require_authenticated),
    service: StrategyDefinitionService = Depends(
        Provide[Container.strategy_definition_service]
    ),
    audit: AuditLogger = Depends(audit_log("strategies_custom")),
) -> StrategyDefinitionRead:
    realm = _resolve_realm_id(auth)
    await audit.info(
        "Create custom strategy",
        {"name": payload.name, "type": payload.type.value},
    )
    try:
        return await service.create(
            payload=payload,
            realmId=realm,
            createdBy=auth.oauth_user_id or auth.api_key,
            apiKey_used=auth.api_key,
            oauth_user_id=auth.oauth_user_id,
        )
    except Exception as e:
        await audit.error(
            "Create custom strategy failed",
            {"name": payload.name, "error": str(e)},
        )
        raise


@router.get(
    "",
    response_model=List[StrategyDefinitionRead],
    summary="List custom strategies for the caller's realm",
)
@inject
async def list_custom_strategies(
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
        pattern="^(DRAFT|PUBLISHED|ARCHIVED)$",
        description="Filter by lifecycle status.",
    ),
    type_filter: Optional[str] = Query(
        default=None,
        alias="type",
        pattern="^(BUILT_IN|DSL_EXTEND|DSL_FULL)$",
        description="Filter by strategy type.",
    ),
    limit: int = Query(default=100, ge=1, le=500),
    auth: AuthContext = Depends(require_authenticated),
    service: StrategyDefinitionService = Depends(
        Provide[Container.strategy_definition_service]
    ),
) -> List[StrategyDefinitionRead]:
    realm = _resolve_realm_id(auth)
    return await service.list_strategies(
        realmId=realm,
        status=status_filter,
        type=type_filter,
        limit=limit,
    )


@router.get(
    "/{id}",
    response_model=StrategyDefinitionRead,
    summary="Get a custom strategy by id (tenant-scoped)",
)
@inject
async def get_custom_strategy(
    id: str,
    auth: AuthContext = Depends(require_authenticated),
    service: StrategyDefinitionService = Depends(
        Provide[Container.strategy_definition_service]
    ),
) -> StrategyDefinitionRead:
    realm = _resolve_realm_id(auth)
    return await service.get_strategy(id=id, realmId=realm)


@router.put(
    "/{id}",
    response_model=StrategyDefinitionRead,
    summary="Edit a custom strategy (forks a new draft when published)",
)
@inject
async def update_custom_strategy(
    id: str,
    payload: StrategyDefinitionUpdate,
    auth: AuthContext = Depends(require_authenticated),
    service: StrategyDefinitionService = Depends(
        Provide[Container.strategy_definition_service]
    ),
    audit: AuditLogger = Depends(audit_log("strategies_custom")),
) -> StrategyDefinitionRead:
    realm = _resolve_realm_id(auth)
    await audit.info("Update custom strategy", {"id": id})
    try:
        return await service.update(
            id=id,
            payload=payload,
            realmId=realm,
            createdBy=auth.oauth_user_id or auth.api_key,
            apiKey_used=auth.api_key,
            oauth_user_id=auth.oauth_user_id,
        )
    except Exception as e:
        await audit.error(
            "Update custom strategy failed",
            {"id": id, "error": str(e)},
        )
        raise


@router.post(
    "/{id}/publish",
    response_model=StrategyDefinitionRead,
    summary="Publish a draft (admin-only)",
)
@inject
async def publish_custom_strategy(
    id: str,
    auth: AuthContext = Depends(require_admin),
    service: StrategyDefinitionService = Depends(
        Provide[Container.strategy_definition_service]
    ),
    audit: AuditLogger = Depends(audit_log("strategies_custom")),
) -> StrategyDefinitionRead:
    realm = _resolve_realm_id(auth)
    await audit.info("Publish custom strategy", {"id": id})
    try:
        return await service.publish(id=id, realmId=realm)
    except Exception as e:
        await audit.error(
            "Publish custom strategy failed",
            {"id": id, "error": str(e)},
        )
        raise


@router.post(
    "/{id}/archive",
    response_model=StrategyDefinitionRead,
    summary="Archive a strategy (admin-only)",
)
@inject
async def archive_custom_strategy(
    id: str,
    auth: AuthContext = Depends(require_admin),
    service: StrategyDefinitionService = Depends(
        Provide[Container.strategy_definition_service]
    ),
    audit: AuditLogger = Depends(audit_log("strategies_custom")),
) -> StrategyDefinitionRead:
    realm = _resolve_realm_id(auth)
    await audit.info("Archive custom strategy", {"id": id})
    try:
        return await service.archive(id=id, realmId=realm)
    except Exception as e:
        await audit.error(
            "Archive custom strategy failed",
            {"id": id, "error": str(e)},
        )
        raise


@router.post(
    "/{id}/simulate",
    response_model=SimulationResponse,
    summary="Dry-run a strategy AST against synthetic or real inputs",
)
@inject
async def simulate_custom_strategy(
    id: str,
    payload: SimulationRequest,
    auth: AuthContext = Depends(require_authenticated),
    service: DslSimulationService = Depends(
        Provide[Container.dsl_simulation_service]
    ),
    audit: AuditLogger = Depends(audit_log("strategies_custom")),
) -> SimulationResponse:
    """
    Run the strategy's AST through the sandbox without persisting any
    UserPoints/Wallet rows. ``mockState`` keys override individual field
    paths (e.g. ``{"user.measurements_count": 5}``) so designers can
    iterate on logic without depending on real production analytics.
    """
    realm = _resolve_realm_id(auth)
    await audit.info(
        "Simulate custom strategy",
        {"id": id, "externalUserId": payload.externalUserId},
    )
    try:
        return await service.simulate(id=id, realmId=realm, request=payload)
    except Exception as e:
        await audit.error(
            "Simulate custom strategy failed",
            {"id": id, "error": str(e)},
        )
        raise
