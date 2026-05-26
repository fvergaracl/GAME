from contextlib import AbstractAsyncContextManager
from typing import Callable, List, Optional
from uuid import UUID

from sqlalchemy import and_, delete as sa_delete, select
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

    async def get_by_user_and_game(
        self, user_id: UUID, game_id: UUID
    ) -> Optional[UserGameConfig]:
        """
        Return the configuration row for a (userId, gameId) pair, or ``None``.
        """
        async with self.session_factory() as session:
            stmt = select(self.model).where(
                and_(
                    self.model.userId == user_id,
                    self.model.gameId == game_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def create_or_update(
        self,
        user_id: UUID,
        game_id: UUID,
        experiment_group: str,
        config_data: Optional[dict],
    ) -> UserGameConfig:
        """
        Insert a new configuration row for (userId, gameId), or update the
        existing one in place. Returns the persisted entity.
        """
        async with self.session_factory() as session:
            stmt = select(self.model).where(
                and_(
                    self.model.userId == user_id,
                    self.model.gameId == game_id,
                )
            )
            entity = (await session.execute(stmt)).scalars().first()
            if entity is None:
                entity = self.model(
                    userId=user_id,
                    gameId=game_id,
                    experimentGroup=experiment_group,
                    configData=config_data,
                )
                session.add(entity)
            else:
                entity.experimentGroup = experiment_group
                entity.configData = config_data
            await session.commit()
            await session.refresh(entity)
            return entity

    async def delete(self, user_id: UUID, game_id: UUID) -> bool:
        """
        Delete the configuration row for a (userId, gameId) pair. Returns
        ``True`` if a row was deleted, ``False`` otherwise.
        """
        async with self.session_factory() as session:
            stmt = select(self.model).where(
                and_(
                    self.model.userId == user_id,
                    self.model.gameId == game_id,
                )
            )
            entity = (await session.execute(stmt)).scalars().first()
            if entity is None:
                return False
            await session.execute(
                sa_delete(self.model).where(self.model.id == entity.id)
            )
            await session.commit()
            return True
