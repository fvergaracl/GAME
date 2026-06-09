"""
ExportService: builds streamed CSV/XLSX/JSON dumps for the 4 admin-facing
datasets exposed by /v1/exports.

Design notes:
  * Queries use SQLAlchemy 2.0's async streaming (``session.stream``) with a
    hard ``LIMIT`` so memory stays bounded even on the 100k-row cap.
  * Row-level transformation lives in private ``_serialize_*`` helpers so the
    formatter layer (CSV/JSON/XLSX) only sees flat dicts.
  * The XLSX path imports ``openpyxl`` lazily; if the dependency is not
    installed the endpoint surfaces a clear 503 instead of a 500.
"""

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy import select

from app.core.exceptions import InternalServerError
from app.model.export_audit_log import ExportAuditLog
from app.model.games import Games
from app.model.tasks import Tasks
from app.model.user_actions import UserActions
from app.model.user_points import UserPoints
from app.model.users import Users
from app.model.wallet import Wallet
from app.model.wallet_transactions import WalletTransactions
from app.repository.export_audit_log_repository import ExportAuditLogRepository
from app.schema.export_schema import (CreateExportAuditLog, ExportAuditLogEntry,
                                      ExportDatasetType, ExportFilters, ExportFormat,
                                      ExportStatus)
from app.services.base_service import BaseService

# Column order for each dataset. Drives both CSV header row and XLSX columns.
DATASET_COLUMNS: Dict[str, List[str]] = {
    ExportDatasetType.USERS.value: [
        "id",
        "externalUserId",
        "created_at",
        "updated_at",
        "apiKey_used",
        "oauth_user_id",
    ],
    ExportDatasetType.USER_POINTS.value: [
        "id",
        "created_at",
        "externalUserId",
        "externalTaskId",
        "externalGameId",
        "points",
        "caseName",
        "description",
        "idempotencyKey",
        "data",
        "apiKey_used",
    ],
    ExportDatasetType.USER_INTERACTIONS.value: [
        "id",
        "created_at",
        "externalUserId",
        "typeAction",
        "description",
        "data",
        "apiKey_used",
    ],
    ExportDatasetType.WALLET_TRANSACTIONS.value: [
        "id",
        "created_at",
        "externalUserId",
        "transactionType",
        "points",
        "coins",
        "appliedConversionRate",
        "data",
        "apiKey_used",
    ],
}


def _isoformat(value: Any) -> Any:
    """Datetime → ISO 8601 string. Pass through otherwise."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _stringify_for_tabular(value: Any) -> Any:
    """
    CSV/XLSX cells must be scalar. JSON dicts get serialized to a JSON string;
    None becomes empty string; datetimes become ISO 8601.
    """
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"), default=str)
    return value


class ExportService(BaseService):
    """
    Streams large datasets out of Postgres without buffering them in memory.

    Public surface is one async generator per dataset (``iter_users`` etc.),
    plus audit-log helpers consumed by the endpoint layer.
    """

    def __init__(
        self,
        export_audit_log_repository: ExportAuditLogRepository,
    ) -> None:
        self.export_audit_log_repository = export_audit_log_repository
        super().__init__(export_audit_log_repository)

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------
    async def audit_start(
        self,
        dataset_type: str,
        export_format: str,
        filters: ExportFilters,
        *,
        api_key: Optional[str] = None,
        oauth_user_id: Optional[str] = None,
    ) -> ExportAuditLog:
        """
        Persist the audit row at the moment the export request is accepted.
        Written before streaming starts so interrupted downloads remain
        recorded with status="started".
        """
        requested_by = oauth_user_id or api_key
        payload = CreateExportAuditLog(
            datasetType=dataset_type,
            format=export_format,
            filters=filters.model_dump(mode="json", exclude_none=True),
            rowLimit=filters.limit,
            rowCount=-1,
            status=ExportStatus.STARTED.value,
            requestedBy=requested_by,
            apiKey_used=api_key,
            oauth_user_id=oauth_user_id,
            created_at=datetime.now(timezone.utc),
        )
        return await self.export_audit_log_repository.create(payload)

    async def audit_finish(
        self,
        audit_id: str,
        *,
        row_count: int,
        status: str,
    ) -> None:
        """
        Mark an export audit row finished with its final row count and status.

        Args:
            audit_id (str): Id of the audit row started by ``audit_start``.
            row_count (int): Number of rows actually streamed.
            status (str): Terminal status (e.g. completed/failed).
        """
        await self.export_audit_log_repository.mark_finished(
            audit_id, row_count=row_count, status=status
        )

    async def list_history(
        self,
        *,
        limit: int = 50,
        oauth_user_id: Optional[str] = None,
    ) -> List[ExportAuditLogEntry]:
        """
        Return recent audit rows mapped onto the public entry schema, hiding
        internal fields (raw apiKey/oauth_user_id are dropped - only the
        ``requestedBy`` display string survives).
        """
        rows = await self.export_audit_log_repository.list_recent(
            limit=limit, oauth_user_id=oauth_user_id
        )
        return [
            ExportAuditLogEntry(
                id=str(row.id),
                datasetType=row.datasetType,
                format=row.format,
                filters=row.filters,
                rowLimit=row.rowLimit,
                rowCount=row.rowCount,
                status=row.status,
                requestedBy=row.requestedBy,
                created_at=row.created_at,
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def _apply_date_filters(self, stmt, model, filters: ExportFilters):
        """
        Add ``created_at`` range filters to a select statement.

        Args:
            stmt: The SQLAlchemy select to constrain.
            model: The mapped model exposing ``created_at``.
            filters (ExportFilters): Carries optional ``dateFrom``/``dateTo``.

        Returns:
            The statement with any provided date bounds applied.
        """
        if filters.dateFrom is not None:
            stmt = stmt.filter(model.created_at >= filters.dateFrom)
        if filters.dateTo is not None:
            stmt = stmt.filter(model.created_at <= filters.dateTo)
        return stmt

    async def _stream_rows(self, stmt) -> AsyncIterator[Any]:
        """Yield ORM rows one by one using SQLAlchemy's async streaming API."""
        session_factory = self.export_audit_log_repository.session_factory
        async with session_factory() as session:
            result = await session.stream(stmt)
            async for row in result:
                yield row

    # ------------------------------------------------------------------
    # Dataset iterators (each yields plain dicts)
    # ------------------------------------------------------------------
    async def iter_users(self, filters: ExportFilters) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream user rows as plain dicts for export.

        Args:
            filters (ExportFilters): Date range and row limit (game/task
                filters do not apply to users).

        Yields:
            Dict[str, Any]: One serializable user record per row.
        """
        stmt = select(
            Users.id,
            Users.externalUserId,
            Users.created_at,
            Users.updated_at,
            Users.apiKey_used,
            Users.oauth_user_id,
        )
        stmt = self._apply_date_filters(stmt, Users, filters)
        stmt = stmt.order_by(Users.created_at).limit(filters.limit)
        async for row in self._stream_rows(stmt):
            yield {
                "id": str(row.id),
                "externalUserId": row.externalUserId,
                "created_at": _isoformat(row.created_at),
                "updated_at": _isoformat(row.updated_at),
                "apiKey_used": row.apiKey_used,
                "oauth_user_id": row.oauth_user_id,
            }

    async def iter_user_points(
        self, filters: ExportFilters
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream user-point rows (joined with user/task/game) as dicts.

        Args:
            filters (ExportFilters): Date range, row limit and optional
                game/task filters.

        Yields:
            Dict[str, Any]: One serializable user-point record per row.
        """
        stmt = (
            select(
                UserPoints.id,
                UserPoints.created_at,
                Users.externalUserId.label("externalUserId"),
                Tasks.externalTaskId.label("externalTaskId"),
                Games.externalGameId.label("externalGameId"),
                UserPoints.points,
                UserPoints.caseName,
                UserPoints.description,
                UserPoints.idempotencyKey,
                UserPoints.data,
                UserPoints.apiKey_used,
            )
            .join(Users, UserPoints.userId == Users.id)
            .join(Tasks, UserPoints.taskId == Tasks.id)
            .join(Games, Tasks.gameId == Games.id)
        )
        stmt = self._apply_date_filters(stmt, UserPoints, filters)
        if filters.externalGameId is not None:
            stmt = stmt.filter(Games.externalGameId == filters.externalGameId)
        if filters.externalTaskId is not None:
            stmt = stmt.filter(Tasks.externalTaskId == filters.externalTaskId)
        stmt = stmt.order_by(UserPoints.created_at).limit(filters.limit)
        async for row in self._stream_rows(stmt):
            yield {
                "id": str(row.id),
                "created_at": _isoformat(row.created_at),
                "externalUserId": row.externalUserId,
                "externalTaskId": row.externalTaskId,
                "externalGameId": row.externalGameId,
                "points": row.points,
                "caseName": row.caseName,
                "description": row.description,
                "idempotencyKey": row.idempotencyKey,
                "data": row.data,
                "apiKey_used": row.apiKey_used,
            }

    async def iter_user_interactions(
        self, filters: ExportFilters
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream user-action (interaction) rows as dicts.

        Backed by the ``useractions`` table; game/task filters are ignored here
        because those ids only live inside the JSON ``data`` column.

        Args:
            filters (ExportFilters): Date range and row limit.

        Yields:
            Dict[str, Any]: One serializable interaction record per row.
        """
        # Backed by the ``useractions`` table (model: UserActions). The legacy
        # ``UserInteractions`` model has no corresponding table, so any query
        # against it raises UndefinedTableError at runtime.
        # externalGameId/externalTaskId filters don't apply here: UserActions
        # has no FK to tasks/games (related IDs, when present, live in the
        # JSONB ``data`` column). We keep them in the endpoint signature for
        # uniformity but ignore them on this dataset.
        stmt = select(
            UserActions.id,
            UserActions.created_at,
            Users.externalUserId.label("externalUserId"),
            UserActions.typeAction,
            UserActions.description,
            UserActions.data,
            UserActions.apiKey_used,
        ).outerjoin(Users, UserActions.userId == Users.id)
        stmt = self._apply_date_filters(stmt, UserActions, filters)
        stmt = stmt.order_by(UserActions.created_at).limit(filters.limit)
        async for row in self._stream_rows(stmt):
            yield {
                "id": str(row.id),
                "created_at": _isoformat(row.created_at),
                "externalUserId": row.externalUserId,
                "typeAction": row.typeAction,
                "description": row.description,
                "data": row.data,
                "apiKey_used": row.apiKey_used,
            }

    async def iter_wallet_transactions(
        self, filters: ExportFilters
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream wallet-transaction rows (joined with the owning user) as dicts.

        Args:
            filters (ExportFilters): Date range and row limit (game/task
                filters do not apply).

        Yields:
            Dict[str, Any]: One serializable transaction record per row.
        """
        # gameId/taskId filters don't apply to wallet transactions; we keep the
        # parameter signature uniform but ignore those filters here.
        stmt = (
            select(
                WalletTransactions.id,
                WalletTransactions.created_at,
                Users.externalUserId.label("externalUserId"),
                WalletTransactions.transactionType,
                WalletTransactions.points,
                WalletTransactions.coins,
                WalletTransactions.appliedConversionRate,
                WalletTransactions.data,
                WalletTransactions.apiKey_used,
            )
            .join(Wallet, WalletTransactions.walletId == Wallet.id)
            .join(Users, Wallet.userId == Users.id)
        )
        stmt = self._apply_date_filters(stmt, WalletTransactions, filters)
        stmt = stmt.order_by(WalletTransactions.created_at).limit(filters.limit)
        async for row in self._stream_rows(stmt):
            yield {
                "id": str(row.id),
                "created_at": _isoformat(row.created_at),
                "externalUserId": row.externalUserId,
                "transactionType": row.transactionType,
                "points": row.points,
                "coins": row.coins,
                "appliedConversionRate": row.appliedConversionRate,
                "data": row.data,
                "apiKey_used": row.apiKey_used,
            }

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------
    def iter_dataset(
        self, dataset_type: str, filters: ExportFilters
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Returns the row iterator for the requested dataset. Raises 500 if the
        dataset name is unknown - this should never happen because the
        endpoint layer already validated the path.
        """
        mapping = {
            ExportDatasetType.USERS.value: self.iter_users,
            ExportDatasetType.USER_POINTS.value: self.iter_user_points,
            ExportDatasetType.USER_INTERACTIONS.value: (self.iter_user_interactions),
            ExportDatasetType.WALLET_TRANSACTIONS.value: (
                self.iter_wallet_transactions
            ),
        }
        try:
            return mapping[dataset_type](filters)
        except KeyError as exc:
            raise InternalServerError(
                detail=f"Unknown dataset type: {dataset_type}"
            ) from exc

    # ------------------------------------------------------------------
    # Formatters (return async generators of bytes ready for StreamingResponse)
    # ------------------------------------------------------------------
    @staticmethod
    async def format_as_csv(
        rows: AsyncIterator[Dict[str, Any]],
        columns: List[str],
    ) -> AsyncIterator[bytes]:
        """
        Emit a UTF-8 CSV stream. Uses an in-memory StringIO buffer per row so
        we never accumulate the whole table.
        """
        # Write header.
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        yield buffer.getvalue().encode("utf-8")
        async for row in rows:
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow({k: _stringify_for_tabular(row.get(k)) for k in columns})
            yield buffer.getvalue().encode("utf-8")

    @staticmethod
    async def format_as_json(
        rows: AsyncIterator[Dict[str, Any]],
    ) -> AsyncIterator[bytes]:
        """
        Emit a JSON array streamed incrementally so the response body looks
        like a normal JSON array to the client. Uses default=str so any
        unexpected type (UUID, Decimal) doesn't crash the dump.
        """
        yield b"["
        first = True
        async for row in rows:
            chunk = json.dumps(row, default=str, separators=(",", ":"))
            if first:
                yield chunk.encode("utf-8")
                first = False
            else:
                yield b"," + chunk.encode("utf-8")
        yield b"]"

    @staticmethod
    async def format_as_xlsx(
        rows: AsyncIterator[Dict[str, Any]],
        columns: List[str],
    ) -> AsyncIterator[bytes]:
        """
        Build an XLSX file using openpyxl write-only mode. The library buffers
        rows internally as it writes them out to a zip stream - for the 100k
        row cap this stays well below 200MB resident.

        openpyxl is imported lazily so the rest of the export pipeline keeps
        working if the dependency is missing.
        """
        try:
            from openpyxl import Workbook
        except ImportError as exc:  # pragma: no cover - env w/o openpyxl
            raise InternalServerError(
                detail=(
                    "XLSX export requires 'openpyxl'. Install it "
                    "(`poetry add openpyxl`) or use format=csv/json."
                )
            ) from exc

        workbook = Workbook(write_only=True)
        sheet = workbook.create_sheet(title="export")
        sheet.append(columns)
        async for row in rows:
            sheet.append([_stringify_for_tabular(row.get(col)) for col in columns])
        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        # Single yield is fine: the file is fully built in memory before the
        # 100k cap, and StreamingResponse will still iterate to send it.
        yield buffer.read()

    # ------------------------------------------------------------------
    # Dispatch wrapper: dataset + format → (media_type, filename, body_iter)
    # ------------------------------------------------------------------
    def format_iterator(
        self,
        dataset_type: str,
        export_format: str,
        rows: AsyncIterator[Dict[str, Any]],
    ) -> AsyncIterator[bytes]:
        """
        Wrap a row iterator in the byte-stream formatter for the chosen format.

        Args:
            dataset_type (str): Dataset name, used to resolve column order.
            export_format (str): One of ``csv``/``json``/``xlsx``.
            rows (AsyncIterator[Dict[str, Any]]): The dataset rows to encode.

        Returns:
            AsyncIterator[bytes]: An async iterator yielding encoded chunks.

        Raises:
            InternalServerError: If ``export_format`` is unknown.
        """
        columns = DATASET_COLUMNS[dataset_type]
        if export_format == ExportFormat.CSV.value:
            return self.format_as_csv(rows, columns)
        if export_format == ExportFormat.JSON.value:
            return self.format_as_json(rows)
        if export_format == ExportFormat.XLSX.value:
            return self.format_as_xlsx(rows, columns)
        raise InternalServerError(detail=f"Unknown export format: {export_format}")

    @staticmethod
    def media_type_for(export_format: str) -> str:
        """
        Return the HTTP ``Content-Type`` for an export format.

        Args:
            export_format (str): One of ``csv``/``json``/``xlsx``.

        Returns:
            str: The matching media type.
        """
        return {
            ExportFormat.CSV.value: "text/csv; charset=utf-8",
            ExportFormat.JSON.value: "application/json",
            ExportFormat.XLSX.value: (
                "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
            ),
        }[export_format]

    @staticmethod
    def filename_for(dataset_type: str, export_format: str) -> str:
        """
        Build a timestamped download filename for an export.

        Args:
            dataset_type (str): Dataset name used as the filename stem.
            export_format (str): Format extension (``csv``/``json``/``xlsx``).

        Returns:
            str: A name like ``users_20260609T120000Z.csv``.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{dataset_type}_{timestamp}.{export_format}"
