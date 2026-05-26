from contextlib import AbstractAsyncContextManager
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import select, update as sa_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.abuse_limit_counter import AbuseLimitCounter
from app.repository.base_repository import BaseRepository


class AbuseLimitCounterRepository(BaseRepository):
    """
    Repository for abuse prevention counters.

    The increment operation is safe under concurrent writes:
    - update existing bucket atomically (`counter = counter + 1`)
    - if bucket does not exist, insert
    - if concurrent insert collides, retry update
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=AbuseLimitCounter,
    ) -> None:
        super().__init__(session_factory, model)

    async def increment_and_get(
        self,
        scope_type: str,
        scope_value: str,
        window_name: str,
        window_start: datetime,
    ) -> int:
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=timezone.utc)

        async with self.session_factory() as session:
            filters = self._build_filters(
                scope_type=scope_type,
                scope_value=scope_value,
                window_name=window_name,
                window_start=window_start,
            )

            update_payload = {
                self.model.counter: self.model.counter + 1,
                self.model.updated_at: datetime.now(timezone.utc),
            }

            updated_rows = (
                await session.execute(
                    sa_update(self.model)
                    .where(*filters)
                    .values(update_payload)
                    .execution_options(synchronize_session=False)
                )
            ).rowcount
            if updated_rows:
                await session.commit()
                return await self._read_counter(session, filters)

            try:
                session.add(
                    self.model(
                        scopeType=scope_type,
                        scopeValue=scope_value,
                        windowName=window_name,
                        windowStart=window_start,
                        counter=1,
                    )
                )
                await session.commit()
                return 1
            except IntegrityError:
                await session.rollback()
                await session.execute(
                    sa_update(self.model)
                    .where(*filters)
                    .values(update_payload)
                    .execution_options(synchronize_session=False)
                )
                await session.commit()
                return await self._read_counter(session, filters)

    def _build_filters(
        self,
        scope_type: str,
        scope_value: str,
        window_name: str,
        window_start: datetime,
    ):
        return (
            self.model.scopeType == scope_type,
            self.model.scopeValue == scope_value,
            self.model.windowName == window_name,
            self.model.windowStart == window_start,
        )

    async def _read_counter(self, session: AsyncSession, filters) -> int:
        value = (
            await session.execute(
                select(self.model.counter).where(*filters)
            )
        ).scalar()
        return int(value or 0)
