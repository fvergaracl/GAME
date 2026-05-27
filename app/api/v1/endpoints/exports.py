"""
Admin-only data export endpoints.

Exposes streaming CSV/XLSX/JSON dumps of the four operational datasets the
business team needs to inspect (users, user-points, user-interactions,
wallet-transactions). Requires a Keycloak OIDC token with the
``AdministratorGAME`` role — plain API keys cannot pull bulk data through
these endpoints by design (see Sprint 1 plan: an API key with realm scope
should not be able to dump cross-tenant data).
"""

from datetime import datetime
from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.container import Container
from app.core.exceptions import ForbiddenError
from app.middlewares.auth_context import (
    AuditLogger,
    AuthContext,
    audit_log,
    get_auth_context,
)
from app.schema.export_schema import (
    ExportDatasetType,
    ExportFilters,
    ExportFormat,
    ExportStatus,
)
from app.services.export_service import ExportService

router = APIRouter(
    prefix="/exports",
    tags=["exports"],
)


async def require_admin(
    auth: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    """
    Reject any caller without the AdministratorGAME role. Exports leak more
    data than any other endpoint in the system, so the bar is OIDC + admin
    only.
    """
    if not auth.is_admin:
        raise ForbiddenError(
            detail=(
                "Data exports require an authenticated administrator. "
                "Sign in with a Keycloak account holding the "
                "AdministratorGAME role."
            )
        )
    return auth


def _build_filters(
    externalGameId: Optional[str],
    externalTaskId: Optional[str],
    dateFrom: Optional[datetime],
    dateTo: Optional[datetime],
    limit: int,
) -> ExportFilters:
    return ExportFilters(
        externalGameId=externalGameId,
        externalTaskId=externalTaskId,
        dateFrom=dateFrom,
        dateTo=dateTo,
        limit=limit,
    )


def _content_disposition(filename: str) -> str:
    return f'attachment; filename="{filename}"'


async def _stream_export(
    *,
    dataset_type: str,
    export_format: ExportFormat,
    filters: ExportFilters,
    service: ExportService,
    audit: AuditLogger,
    auth: AuthContext,
) -> StreamingResponse:
    """
    Common pipeline shared by every dataset endpoint:
      1. Persist the audit row (status=started) so an interrupted download is
         still recorded.
      2. Wrap the dataset iterator with a row counter.
      3. Wrap the formatter generator so we mark the audit row completed
         (or failed) when the response finishes.
    """
    audit_row = await service.audit_start(
        dataset_type=dataset_type,
        export_format=export_format.value,
        filters=filters,
        api_key=auth.api_key,
        oauth_user_id=auth.oauth_user_id,
    )
    await audit.info(
        "Export started",
        {
            "auditId": str(audit_row.id),
            "datasetType": dataset_type,
            "format": export_format.value,
            "filters": filters.model_dump(mode="json", exclude_none=True),
        },
    )

    row_counter = {"n": 0}

    async def _counted_rows():
        async for row in service.iter_dataset(dataset_type, filters):
            row_counter["n"] += 1
            yield row

    body_iter = service.format_iterator(
        dataset_type, export_format.value, _counted_rows()
    )

    async def _wrapped():
        try:
            async for chunk in body_iter:
                yield chunk
        except Exception as exc:  # pragma: no cover - safety net
            await service.audit_finish(
                str(audit_row.id),
                row_count=row_counter["n"],
                status=ExportStatus.FAILED.value,
            )
            await audit.error(
                "Export failed",
                {"auditId": str(audit_row.id), "error": str(exc)},
            )
            raise
        await service.audit_finish(
            str(audit_row.id),
            row_count=row_counter["n"],
            status=ExportStatus.COMPLETED.value,
        )
        await audit.success(
            "Export completed",
            {
                "auditId": str(audit_row.id),
                "rowCount": row_counter["n"],
            },
        )

    filename = service.filename_for(dataset_type, export_format.value)
    return StreamingResponse(
        _wrapped(),
        media_type=service.media_type_for(export_format.value),
        headers={"Content-Disposition": _content_disposition(filename)},
    )


_format_query = Query(
    default=ExportFormat.CSV,
    description="Output format. One of csv | xlsx | json.",
)
_external_game_id_query = Query(
    default=None,
    description="Filter by externalGameId.",
)
_external_task_id_query = Query(
    default=None,
    description="Filter by externalTaskId.",
)
_date_from_query = Query(
    default=None,
    description="Inclusive lower bound for created_at (ISO 8601).",
)
_date_to_query = Query(
    default=None,
    description="Inclusive upper bound for created_at (ISO 8601).",
)
_limit_query = Query(
    default=10_000,
    ge=1,
    le=100_000,
    description="Maximum number of rows to emit (hard cap: 100,000).",
)


@router.get(
    "/users",
    summary="Export users",
    description=(
        "Stream the users table as CSV/XLSX/JSON. "
        "Admin-only. Hard cap of 100,000 rows per request."
    ),
    response_class=StreamingResponse,
)
@inject
async def export_users(
    format: ExportFormat = _format_query,
    dateFrom: Optional[datetime] = _date_from_query,
    dateTo: Optional[datetime] = _date_to_query,
    limit: int = _limit_query,
    auth: AuthContext = Depends(require_admin),
    service: ExportService = Depends(Provide[Container.export_service]),
    audit: AuditLogger = Depends(audit_log("exports")),
):
    filters = _build_filters(None, None, dateFrom, dateTo, limit)
    return await _stream_export(
        dataset_type=ExportDatasetType.USERS.value,
        export_format=format,
        filters=filters,
        service=service,
        audit=audit,
        auth=auth,
    )


@router.get(
    "/user-points",
    summary="Export user points",
    description=(
        "Stream user-point assignments joined with externalUserId, "
        "externalTaskId and externalGameId. Supports filtering by game, "
        "task and date range. Admin-only."
    ),
    response_class=StreamingResponse,
)
@inject
async def export_user_points(
    format: ExportFormat = _format_query,
    externalGameId: Optional[str] = _external_game_id_query,
    externalTaskId: Optional[str] = _external_task_id_query,
    dateFrom: Optional[datetime] = _date_from_query,
    dateTo: Optional[datetime] = _date_to_query,
    limit: int = _limit_query,
    auth: AuthContext = Depends(require_admin),
    service: ExportService = Depends(Provide[Container.export_service]),
    audit: AuditLogger = Depends(audit_log("exports")),
):
    filters = _build_filters(
        externalGameId, externalTaskId, dateFrom, dateTo, limit
    )
    return await _stream_export(
        dataset_type=ExportDatasetType.USER_POINTS.value,
        export_format=format,
        filters=filters,
        service=service,
        audit=audit,
        auth=auth,
    )


@router.get(
    "/user-interactions",
    summary="Export user interactions",
    description=(
        "Stream user-interaction events (achievements, task events, etc.). "
        "Supports filtering by game, task and date range. Admin-only."
    ),
    response_class=StreamingResponse,
)
@inject
async def export_user_interactions(
    format: ExportFormat = _format_query,
    externalGameId: Optional[str] = _external_game_id_query,
    externalTaskId: Optional[str] = _external_task_id_query,
    dateFrom: Optional[datetime] = _date_from_query,
    dateTo: Optional[datetime] = _date_to_query,
    limit: int = _limit_query,
    auth: AuthContext = Depends(require_admin),
    service: ExportService = Depends(Provide[Container.export_service]),
    audit: AuditLogger = Depends(audit_log("exports")),
):
    filters = _build_filters(
        externalGameId, externalTaskId, dateFrom, dateTo, limit
    )
    return await _stream_export(
        dataset_type=ExportDatasetType.USER_INTERACTIONS.value,
        export_format=format,
        filters=filters,
        service=service,
        audit=audit,
        auth=auth,
    )


@router.get(
    "/wallet-transactions",
    summary="Export wallet transactions",
    description=(
        "Stream wallet transactions joined with the owning externalUserId. "
        "Supports filtering by date range. Admin-only."
    ),
    response_class=StreamingResponse,
)
@inject
async def export_wallet_transactions(
    format: ExportFormat = _format_query,
    dateFrom: Optional[datetime] = _date_from_query,
    dateTo: Optional[datetime] = _date_to_query,
    limit: int = _limit_query,
    auth: AuthContext = Depends(require_admin),
    service: ExportService = Depends(Provide[Container.export_service]),
    audit: AuditLogger = Depends(audit_log("exports")),
):
    filters = _build_filters(None, None, dateFrom, dateTo, limit)
    return await _stream_export(
        dataset_type=ExportDatasetType.WALLET_TRANSACTIONS.value,
        export_format=format,
        filters=filters,
        service=service,
        audit=audit,
        auth=auth,
    )
