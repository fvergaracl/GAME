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

from datetime import datetime, timezone
from typing import List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Path, Query, status

from app.core.config import configs
from app.core.container import Container
from app.core.exceptions import ForbiddenError
from app.engine.dsl_templates.loader import load_user_templates
from app.engine.dsl_validator import validate_ast
from app.middlewares.auth_context import (AuditLogger, AuthContext, audit_log,
                                          get_auth_context)
from app.model.strategy_definition import StrategyDefinitionType
from app.schema.dsl_schema import (InlineSimulationRequest, SimulationRequest,
                                   SimulationResponse)
from app.schema.strategy_definition_schema import (StrategyDefinitionCreate,
                                                   StrategyDefinitionImport,
                                                   StrategyDefinitionRead,
                                                   StrategyDefinitionUpdate,
                                                   StrategyTemplateRead,
                                                   StrategyUsageRead)
from app.services.dsl_simulation_service import DslSimulationService
from app.services.strategy_definition_service import StrategyDefinitionService
from app.services.strategy_service import StrategyService

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


def _ensure_parent_strategy_exists(
    payload_type,
    parent_strategy_id,
    strategy_service: StrategyService,
) -> None:
    """Sprint 7: when a DSL_EXTEND row is created/updated, verify the
    referenced parentStrategyId actually resolves to a built-in. The
    service-level _validate_payload only checks presence/absence;
    cross-checking the registry has to live at the endpoint layer
    because StrategyDefinitionService can't import StrategyService
    without creating a circular dep (see comment at
    strategy_definition_service.py:85-88).

    Raises NotFoundError (404) with a clear message when the parent
    doesn't exist; no-op for non-EXTEND payloads or missing
    parentStrategyId (the service validator will reject that earlier).
    """
    if payload_type != StrategyDefinitionType.DSL_EXTEND:
        return
    if not parent_strategy_id:
        return
    # ``get_strategy_by_id`` raises NotFoundError(404) when the id is
    # not in the registry; we let that bubble up as the HTTP response.
    strategy_service.get_strategy_by_id(parent_strategy_id)


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
    strategy_service: StrategyService = Depends(Provide[Container.strategy_service]),
    audit: AuditLogger = Depends(audit_log("strategies_custom")),
) -> StrategyDefinitionRead:
    """
    Create a new custom-strategy draft in the caller's realm.

    Validates that the referenced parent strategy exists (for DSL-extend
    types) and persists the draft, recording audit entries on success/failure.

    Args:
        payload (StrategyDefinitionCreate): The strategy definition to create.
        auth (AuthContext): Authenticated caller context.
        service (StrategyDefinitionService): Injected definition service.
        strategy_service (StrategyService): Injected registry service used to
            validate the parent strategy.
        audit (AuditLogger): Request-scoped audit logger.

    Returns:
        StrategyDefinitionRead: The newly created draft.
    """
    realm = _resolve_realm_id(auth)
    await audit.info(
        "Create custom strategy",
        {"name": payload.name, "type": payload.type.value},
    )
    try:
        _ensure_parent_strategy_exists(
            payload.type,
            payload.parentStrategyId,
            strategy_service,
        )
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
    """
    List custom strategies belonging to the caller's realm.

    Args:
        status_filter (Optional[str]): Optional lifecycle filter
            (DRAFT/PUBLISHED/ARCHIVED).
        type_filter (Optional[str]): Optional type filter
            (BUILT_IN/DSL_EXTEND/DSL_FULL).
        limit (int): Maximum rows to return (1–500).
        auth (AuthContext): Authenticated caller context.
        service (StrategyDefinitionService): Injected definition service.

    Returns:
        List[StrategyDefinitionRead]: The matching strategy definitions.
    """
    realm = _resolve_realm_id(auth)
    return await service.list_strategies(
        realmId=realm,
        status=status_filter,
        type=type_filter,
        limit=limit,
    )


@router.get(
    "/templates",
    response_model=List[StrategyTemplateRead],
    summary="List built-in user-facing templates (Sprint 8)",
)
async def list_strategy_templates(
    auth: AuthContext = Depends(require_authenticated),
) -> List[StrategyTemplateRead]:
    """Return the curated templates that seed the editor's
    "Usar una plantilla" CTA. Tenant-agnostic — every authenticated
    caller sees the same list. The loader validates ASTs at boot, so
    everything returned here is guaranteed to round-trip through the
    editor and through ``POST /import`` without further checks.
    """
    return load_user_templates()


@router.post(
    "/import",
    response_model=StrategyDefinitionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import a strategy bundle as a new DRAFT (Sprint 8)",
)
@inject
async def import_custom_strategy(
    payload: StrategyDefinitionImport,
    auth: AuthContext = Depends(require_authenticated),
    service: StrategyDefinitionService = Depends(
        Provide[Container.strategy_definition_service]
    ),
    strategy_service: StrategyService = Depends(Provide[Container.strategy_service]),
    audit: AuditLogger = Depends(audit_log("strategy_import")),
) -> StrategyDefinitionRead:
    """
    Persist a strategy bundle produced by the dashboard's
    "Exportar JSON" action (or hand-authored equivalent).

    Differs from ``POST /`` in two ways:
      * AST is validated up-front so a malformed payload returns a
        ``DslValidationError`` before any DB lookup.
      * On a name collision in the same realm the import is renamed
        ``"<name> (importada YYYY-MM-DD)"`` instead of failing with
        ``DuplicatedError``. Import has to be idempotent enough for a
        support engineer to retry without first deleting the prior
        attempt.
    """
    realm = _resolve_realm_id(auth)
    await audit.info(
        "Import custom strategy",
        {"name": payload.name, "type": payload.type.value},
    )
    try:
        # Validate AST before any DB roundtrip so the caller gets a
        # precise error pointing at the offending node.
        validate_ast(payload.astJson)
        _ensure_parent_strategy_exists(
            payload.type,
            payload.parentStrategyId,
            strategy_service,
        )

        # Auto-rename on name collision so a re-import is idempotent.
        # Without this the unique constraint on (realmId, name, version)
        # would trip inside service.create with a confusing 400.
        target_name = payload.name
        if await service.name_exists(realmId=realm, name=target_name):
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            target_name = f"{payload.name} (importada {today})"

        create_payload = StrategyDefinitionCreate(
            name=target_name,
            description=payload.description,
            type=payload.type,
            parentStrategyId=payload.parentStrategyId,
            astJson=payload.astJson,
            blocklyXml=payload.blocklyXml,
            experimentTag=payload.experimentTag,
        )
        return await service.create(
            payload=create_payload,
            realmId=realm,
            createdBy=auth.oauth_user_id or auth.api_key,
            apiKey_used=auth.api_key,
            oauth_user_id=auth.oauth_user_id,
        )
    except Exception as e:
        await audit.error(
            "Import custom strategy failed",
            {"name": payload.name, "error": str(e)},
        )
        raise


@router.post(
    "/simulate",
    response_model=SimulationResponse,
    summary="Dry-run an inline AST without persisting a draft (Sprint 5)",
)
@inject
async def simulate_inline_strategy(
    payload: InlineSimulationRequest,
    auth: AuthContext = Depends(require_authenticated),
    service: DslSimulationService = Depends(Provide[Container.dsl_simulation_service]),
    audit: AuditLogger = Depends(audit_log("strategies_custom")),
) -> SimulationResponse:
    """
    Run an AST supplied inline through the sandbox without any DB lookup
    or persistence (fix C7).

    The editor's "Probar" button previously had to create a hidden DRAFT
    just to obtain an id for ``/{id}/simulate``, leaving orphan rows after
    every test iteration. This route takes the AST directly so simulation
    tests the exact blocks on the canvas — unsaved edits included — and
    leaves no trace in the database. Declared before the ``/{id}`` routes
    so the literal ``/simulate`` path is matched first.
    """
    realm = _resolve_realm_id(auth)
    await audit.info(
        "Simulate inline strategy",
        {"externalUserId": payload.externalUserId},
    )
    try:
        return await service.simulate_inline(realmId=realm, request=payload)
    except Exception as e:
        await audit.error(
            "Simulate inline strategy failed",
            {"error": str(e)},
        )
        raise


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
    """
    Fetch a single custom strategy by id, scoped to the caller's realm.

    Args:
        id (str): Strategy definition identifier.
        auth (AuthContext): Authenticated caller context.
        service (StrategyDefinitionService): Injected definition service.

    Returns:
        StrategyDefinitionRead: The requested strategy definition.
    """
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
    strategy_service: StrategyService = Depends(Provide[Container.strategy_service]),
    audit: AuditLogger = Depends(audit_log("strategies_custom")),
) -> StrategyDefinitionRead:
    """
    Edit a custom strategy, forking a new draft when it is already published.

    Args:
        id (str): Strategy definition identifier.
        payload (StrategyDefinitionUpdate): The fields to update.
        auth (AuthContext): Authenticated caller context.
        service (StrategyDefinitionService): Injected definition service.
        strategy_service (StrategyService): Injected registry service used to
            validate any referenced parent strategy.
        audit (AuditLogger): Request-scoped audit logger.

    Returns:
        StrategyDefinitionRead: The updated (or newly forked) draft.
    """
    realm = _resolve_realm_id(auth)
    await audit.info("Update custom strategy", {"id": id})
    try:
        # Sprint 7: same registry check as create — only relevant when
        # the PUT explicitly carries type+parentStrategyId.
        _ensure_parent_strategy_exists(
            payload.type,
            payload.parentStrategyId,
            strategy_service,
        )
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
    """
    Publish a draft strategy so it becomes usable by games (admin-only).

    Args:
        id (str): Strategy definition identifier.
        auth (AuthContext): Authenticated admin context.
        service (StrategyDefinitionService): Injected definition service.
        audit (AuditLogger): Request-scoped audit logger.

    Returns:
        StrategyDefinitionRead: The published strategy definition.
    """
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
    """
    Archive a strategy so it can no longer be assigned (admin-only).

    Args:
        id (str): Strategy definition identifier.
        auth (AuthContext): Authenticated admin context.
        service (StrategyDefinitionService): Injected definition service.
        audit (AuditLogger): Request-scoped audit logger.

    Returns:
        StrategyDefinitionRead: The archived strategy definition.
    """
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


@router.get(
    "/{id}/versions",
    response_model=List[StrategyDefinitionRead],
    summary="List the version history of a strategy family (Sprint 9)",
)
@inject
async def list_strategy_versions(
    id: str,
    auth: AuthContext = Depends(require_authenticated),
    service: StrategyDefinitionService = Depends(
        Provide[Container.strategy_definition_service]
    ),
) -> List[StrategyDefinitionRead]:
    """
    Return every persisted version (DRAFT/PUBLISHED/ARCHIVED) of the
    family that contains ``id``, newest version first.

    Tenant-scoped: only versions in the caller's realm are returned;
    cross-realm probing 404s on the seed id rather than leaking that
    other tenants own a same-named strategy.
    """
    realm = _resolve_realm_id(auth)
    return await service.list_versions(id=id, realmId=realm)


@router.get(
    "/{id}/usage",
    response_model=StrategyUsageRead,
    summary="List games/tasks assigned to this strategy (Sprint 6)",
)
@inject
async def get_custom_strategy_usage(
    id: str,
    auth: AuthContext = Depends(require_authenticated),
    service: StrategyDefinitionService = Depends(
        Provide[Container.strategy_definition_service]
    ),
) -> StrategyUsageRead:
    """
    Reverse lookup of a strategy's consumers (Sprint 6).

    Returns the games and tasks currently assigned to this exact
    strategy version plus their counts, so the dashboard can preview the
    blast radius before reassigning, archiving or rolling back — and
    drive a bulk reassignment of all of them.
    """
    realm = _resolve_realm_id(auth)
    return await service.get_usage(id=id, realmId=realm)


@router.post(
    "/{id}/rollback/{version}",
    response_model=StrategyDefinitionRead,
    summary="Roll back to a previous version (admin-only, Sprint 9)",
)
@inject
async def rollback_strategy(
    id: str,
    version: int = Path(..., ge=1),
    auth: AuthContext = Depends(require_admin),
    service: StrategyDefinitionService = Depends(
        Provide[Container.strategy_definition_service]
    ),
    audit: AuditLogger = Depends(audit_log("strategies_custom")),
) -> StrategyDefinitionRead:
    """
    Promote ``version`` back to PUBLISHED in the family that contains
    ``id`` and cascade the reassignment to every Games/Tasks row that
    pointed at the previously-published UUID.

    Audit log captures the cascade counts so an operator can verify
    after-the-fact how many consumers were redirected — the response
    body contains only the newly-published strategy.
    """
    realm = _resolve_realm_id(auth)
    await audit.info(
        "Rollback custom strategy",
        {"id": id, "target_version": version},
    )
    try:
        result = await service.rollback(id=id, target_version=version, realmId=realm)
        await audit.success(
            "Rollback custom strategy successful",
            {
                "id": id,
                "target_version": version,
                "promoted_id": result.strategy.id,
                "games_reassigned": result.games_reassigned,
                "tasks_reassigned": result.tasks_reassigned,
            },
        )
        return result.strategy
    except Exception as e:
        await audit.error(
            "Rollback custom strategy failed",
            {
                "id": id,
                "target_version": version,
                "error": str(e),
            },
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
    service: DslSimulationService = Depends(Provide[Container.dsl_simulation_service]),
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
