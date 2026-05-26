from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.oauth_users import OAuthUsers
from app.repository.base_repository import BaseRepository


class OAuthUsersRepository(BaseRepository):
    """
    Repository class for OAuth users.

    Attributes:
        session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for OAuth users.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=OAuthUsers,
    ) -> None:
        """
        Initializes the OAuthUsersRepository with the provided session
          factory and model.

        Args:
            session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
              The session factory.
            model: The SQLAlchemy model class for OAuth users.
        """
        super().__init__(session_factory, model)

    async def get_user_by_sub(self, sub: str):
        """
        Get a user by their sub.

        Args:
            sub: The sub of the user to get (provider_user_id)

        Returns:
            The user with the provided sub.
        """
        async with self.session_factory() as session:
            stmt = select(self.model).filter_by(provider_user_id=sub)
            return (await session.execute(stmt)).scalars().first()
