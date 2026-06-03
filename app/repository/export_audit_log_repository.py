from contextlib import AbstractAsyncContextManager
from typing import Callable, List, Optional

from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.export_audit_log import ExportAuditLog
from app.repository.base_repository import BaseRepository


class ExportAuditLogRepository(BaseRepository):
    """
    Repository for ExportAuditLog rows.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=ExportAuditLog,
    ) -> None:
        super().__init__(session_factory, model)

    async def mark_finished(
        self,
        audit_id: str,
        *,
        row_count: int,
        status: str,
    ) -> None:
        """
        Update an existing audit row with the final row count and status.
        Run after the stream finishes (or fails) so that interrupted downloads
        keep their initial "started" marker.
        """
        async with self.session_factory() as session:
            await session.execute(
                sa_update(self.model)
                .where(self.model.id == audit_id)
                .values(rowCount=row_count, status=status)
            )
            await session.commit()

    async def list_recent(
        self,
        *,
        limit: int = 50,
        oauth_user_id: Optional[str] = None,
    ) -> List[ExportAuditLog]:
        """
        Return audit rows most recent first.

        When ``oauth_user_id`` is provided the list is scoped to that user;
        otherwise (admin view) all rows are returned. Capped at 200 to keep
        the response small enough for the history table.
        """
        # NULLS LAST so historical rows written before the audit_start
        # client-side timestamp fix don't dominate the top of the list.
        stmt = select(self.model).order_by(self.model.created_at.desc().nullslast())
        if oauth_user_id is not None:
            stmt = stmt.where(self.model.oauth_user_id == oauth_user_id)
        stmt = stmt.limit(min(max(limit, 1), 200))
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return list(result.scalars().all())
