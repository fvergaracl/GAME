from contextlib import AbstractAsyncContextManager
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import select
from sqlalchemy import update as sa_update
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
        """
        Atomically increment a rate-limit bucket and return its new value.

        Concurrency-safe: it first tries an atomic ``counter = counter + 1``
        update; if the bucket does not yet exist it inserts it, and if a
        concurrent insert collides it rolls back and retries the update. The
        ``window_start`` is normalized to UTC.

        Args:
            scope_type (str): Dimension being limited (e.g. ``"ip"``,
                ``"api_key"``).
            scope_value (str): Concrete value within ``scope_type``.
            window_name (str): Name of the limit window (e.g. ``"per_minute"``).
            window_start (datetime): Start of the bucket's time window.

        Returns:
            int: The counter value after this increment.
        """
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
        """
        Build the equality filters that uniquely identify a counter bucket.

        Returns:
            tuple: SQLAlchemy boolean expressions for scope type/value,
            window name and window start, used in ``WHERE`` clauses.
        """
        return (
            self.model.scopeType == scope_type,
            self.model.scopeValue == scope_value,
            self.model.windowName == window_name,
            self.model.windowStart == window_start,
        )

    async def _read_counter(self, session: AsyncSession, filters) -> int:
        """
        Read the current counter value for a bucket within ``session``.

        Args:
            session (AsyncSession): Active session to query within.
            filters: Bucket-identifying filters from :meth:`_build_filters`.

        Returns:
            int: The stored counter, or ``0`` when the bucket is absent.
        """
        value = (
            await session.execute(select(self.model.counter).where(*filters))
        ).scalar()
        return int(value or 0)
