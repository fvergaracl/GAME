from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.model.game_params import GamesParams
from app.repository.base_repository import BaseRepository


class GameParamsRepository(BaseRepository):
    """
    Repository class for game parameters.

    Attributes:
        session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for game parameters.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=GamesParams,
    ) -> None:
        """
        Initializes the GameParamsRepository with the provided session factory
          and model.

        Args:
            session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
              The session factory.
            model: The SQLAlchemy model class for game parameters.
        """
        super().__init__(session_factory, model)

    async def patch_game_params_by_id(self, id: str, schema):
        """
        Updates game parameters by their ID.
        """
        async with self.session_factory() as session:
            stmt = select(self.model).filter(self.model.id == id)
            game_params_model = (await session.execute(stmt)).scalars().first()

            if game_params_model:
                for key, value in schema.model_dump(exclude_none=True).items():
                    setattr(game_params_model, key, value)

                await session.commit()
                target_id = game_params_model.id

            else:
                raise NotFoundError(f"GameParams not found (id) : {id}")

        return await self.read_by_id(
            target_id,
            not_found_message=f"GameParams not found (id) : {target_id}",
        )
