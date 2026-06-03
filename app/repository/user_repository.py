from contextlib import AbstractAsyncContextManager
from typing import Callable, Optional

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.model.users import Users
from app.repository.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """
    Repository class for users.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=Users,
    ) -> None:
        super().__init__(session_factory, model)

    async def create_user_by_externalUserId(
        self,
        externalUserId: str,
        oauth_user_id: Optional[str] = None,
    ) -> Users:
        """
        Creates a new user with the provided external user ID.

        Concurrency-safe: when a parallel transaction inserts the same
        externalUserId first, returns the already-existing row instead of
        raising IntegrityError to the caller.
        """
        async with self.session_factory() as session:
            user = Users(externalUserId=externalUserId, oauth_user_id=oauth_user_id)
            session.add(user)
            try:
                await session.commit()
                await session.refresh(user)
                return user
            except IntegrityError:
                await session.rollback()
                existing = (
                    (
                        await session.execute(
                            select(self.model).filter_by(externalUserId=externalUserId)
                        )
                    )
                    .scalars()
                    .first()
                )
                if existing is not None:
                    return existing
                raise

    async def get_or_create_by_externalUserId(
        self,
        externalUserId: str,
        oauth_user_id: Optional[str] = None,
        session: Optional[AsyncSession] = None,
        auto_commit: bool = True,
    ) -> Users:
        """
        Returns an existing user by externalUserId or creates it atomically
        via ``INSERT ... ON CONFLICT DO UPDATE``.
        """
        if session is None and not auto_commit:
            raise ValueError(
                "auto_commit=False requires an external session managed by the caller."
            )
        if session is None:
            async with self.session_factory() as managed_session:
                return await self.get_or_create_by_externalUserId(
                    externalUserId=externalUserId,
                    oauth_user_id=oauth_user_id,
                    session=managed_session,
                    auto_commit=auto_commit,
                )

        users_table = self.model.__table__
        insert_values = {
            "externalUserId": externalUserId,
            "oauth_user_id": oauth_user_id,
        }
        insert_stmt = insert(users_table).values(**insert_values)

        update_values = {"updated_at": func.now()}
        if oauth_user_id is not None:
            update_values["oauth_user_id"] = oauth_user_id

        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[users_table.c.externalUserId],
            set_=update_values,
        ).returning(users_table.c.id)

        user_id = (await session.execute(upsert_stmt)).scalar_one()
        if auto_commit:
            await session.commit()
        else:
            await session.flush()

        user = (
            (await session.execute(select(self.model).filter(self.model.id == user_id)))
            .scalars()
            .first()
        )
        if user is None:
            raise NotFoundError(
                detail=f"User not found after upsert by externalUserId: {externalUserId}"
            )
        return user
