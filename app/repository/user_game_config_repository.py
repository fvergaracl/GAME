from contextlib import AbstractAsyncContextManager
from typing import Callable, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.user_game_config import UserGameConfig
from app.repository.base_repository import BaseRepository


class UserGameConfigRepository(BaseRepository):
    """
    Repository class for managing user-specific game configurations.

    Attributes:
        session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for user game configurations.
    """

    def __init__(
        self, session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]]
    ) -> None:
        """
        Initializes the UserGameConfigRepository.

        Args:
            session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
              The session factory.
        """
        super().__init__(session_factory, UserGameConfig)

    async def get_all_users_by_gameId(self, gameId: str) -> List[UserGameConfig]:
        """
        Get all users by gameId.
        """
        async with self.session_factory() as session:
            stmt = select(self.model).filter_by(gameId=gameId)
            return (await session.execute(stmt)).scalars().all()
