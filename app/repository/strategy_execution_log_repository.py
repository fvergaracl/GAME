"""
Repository for ``StrategyExecutionLog`` rows (Sprint 11).

Writes are best-effort: the engine never blocks scoring on the audit
log, so the service layer wraps the insert in its own try/except. The
read methods power the runbook UI and the post-mortem command-line
helpers.
"""

from contextlib import AbstractAsyncContextManager
from typing import Callable, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.strategy_execution_log import StrategyExecutionLog
from app.repository.base_repository import BaseRepository


class StrategyExecutionLogRepository(BaseRepository):
    def __init__(
        self,
        session_factory: Callable[
            ..., AbstractAsyncContextManager[AsyncSession]
        ],
        model=StrategyExecutionLog,
    ) -> None:
        super().__init__(session_factory, model)

    async def insert_row(self, row: StrategyExecutionLog) -> None:
        """
        Insert a pre-built model instance directly. Bypasses
        ``BaseRepository.create`` because we don't have a pydantic
        schema for these -- the row is assembled by the observer
        from interpreter output and persisted as-is.
        """
        async with self.session_factory() as session:
            session.add(row)
            await session.commit()

    async def list_for_strategy(
        self,
        *,
        strategyId: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[StrategyExecutionLog]:
        """
        Most-recent-first listing for the runbook view.

        ``status`` filter is the common "show me the failures" use
        case from the runbook. The result is capped at 200 so the
        JSON payload stays small even when the operator forgets to
        pass ``limit``.
        """
        stmt = (
            select(self.model)
            .where(self.model.strategyId == strategyId)
            .order_by(self.model.created_at.desc().nullslast())
        )
        if status is not None:
            stmt = stmt.where(self.model.status == status)
        stmt = stmt.limit(min(max(limit, 1), 200))
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return list(result.scalars().all())
