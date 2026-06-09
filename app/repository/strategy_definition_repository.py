"""
Repository for :class:`StrategyDefinition`.

Encapsulates the versioning queries the service relies on: max-version
lookup, status transitions, and tenant-scoped reads. Heavier business
logic (forking drafts on update, archiving published siblings on
publish) is intentionally left to the service so this layer stays a thin
SQL adapter.
"""

from contextlib import AbstractAsyncContextManager
from datetime import datetime
from typing import Callable, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.strategy_definition import StrategyDefinition, StrategyDefinitionStatus
from app.repository.base_repository import BaseRepository


class StrategyDefinitionRepository(BaseRepository):
    """
    Async repository for the ``strategydefinition`` table.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=StrategyDefinition,
    ) -> None:
        super().__init__(session_factory, model)

    async def list_for_realm(
        self,
        *,
        realmId: Optional[str],
        status: Optional[str] = None,
        type: Optional[str] = None,
        limit: int = 100,
    ) -> List[StrategyDefinition]:
        """
        List rows visible to a tenant, most recent first.

        ``realmId=None`` is treated as "global"; callers that want every
        row across realms must pass it explicitly via a separate admin
        helper (not implemented yet - Sprint 3 keeps tenancy strict).
        """
        stmt = select(self.model).where(self.model.realmId == realmId)
        if status is not None:
            stmt = stmt.where(self.model.status == status)
        if type is not None:
            stmt = stmt.where(self.model.type == type)
        stmt = stmt.order_by(self.model.name.asc(), self.model.version.desc()).limit(
            max(1, min(limit, 500))
        )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_for_realm(
        self,
        *,
        id: str,
        realmId: Optional[str],
    ) -> Optional[StrategyDefinition]:
        """
        Fetch one row scoped by id + tenant. Returns ``None`` when the row
        belongs to another tenant; the service maps that to a 404 so we
        don't leak existence across realms.
        """
        stmt = select(self.model).where(
            and_(self.model.id == id, self.model.realmId == realmId)
        )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_versions(
        self,
        *,
        realmId: Optional[str],
        name: str,
    ) -> List[StrategyDefinition]:
        """
        Return every row in a ``(realmId, name)`` family, newest version
        first. Used by the history endpoint planned for Sprint 9 and
        already useful from the service when looking for the latest draft
        or published sibling.
        """
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.realmId == realmId,
                    self.model.name == name,
                )
            )
            .order_by(self.model.version.desc())
        )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_max_version(
        self,
        *,
        realmId: Optional[str],
        name: str,
    ) -> int:
        """
        Highest version number for a ``(realmId, name)`` family, or 0 if
        the family does not exist yet. The service uses this to allocate
        the next draft version atomically.
        """
        stmt = select(func.max(self.model.version)).where(
            and_(
                self.model.realmId == realmId,
                self.model.name == name,
            )
        )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            value = result.scalar_one_or_none()
            return int(value or 0)

    async def get_published(
        self,
        *,
        realmId: Optional[str],
        name: str,
    ) -> Optional[StrategyDefinition]:
        """Return the currently published row of a family, or ``None``."""
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.realmId == realmId,
                    self.model.name == name,
                    self.model.status == StrategyDefinitionStatus.PUBLISHED.value,
                )
            )
            .limit(1)
        )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_version(
        self,
        *,
        realmId: Optional[str],
        name: str,
        version: int,
    ) -> Optional[StrategyDefinition]:
        """
        Fetch a specific ``(realmId, name, version)`` row.

        Used by the rollback flow (Sprint 9) to locate the target version
        being promoted back to PUBLISHED. Returns ``None`` when the version
        does not exist in the family; the service maps that to a 404 so we
        don't leak cross-family info.
        """
        stmt = select(self.model).where(
            and_(
                self.model.realmId == realmId,
                self.model.name == name,
                self.model.version == version,
            )
        )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.scalars().first()

    async def set_status(
        self,
        *,
        id: str,
        status: str,
        publishedAt: Optional[datetime] = None,
    ) -> None:
        """Bulk-set the status (and ``publishedAt`` on PUBLISHED)."""
        values = {"status": status}
        if publishedAt is not None:
            values["publishedAt"] = publishedAt
        async with self.session_factory() as session:
            await session.execute(
                sa_update(self.model).where(self.model.id == id).values(**values)
            )
            await session.commit()
