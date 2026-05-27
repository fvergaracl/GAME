from contextlib import AbstractAsyncContextManager
from typing import Callable

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
