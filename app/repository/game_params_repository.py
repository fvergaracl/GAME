from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.model.game_params import GamesParams
from app.repository.base_repository import BaseRepository


class GameParamsRepository(BaseRepository):
    """
    Repository class for game parameters.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for game parameters.
    """

    def __init__(
            self,
            session_factory: Callable[..., AbstractContextManager[Session]],
            model=GamesParams) -> None:
        """
        Initializes the GameParamsRepository with the provided session factory
          and model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for game parameters.
        """
        super().__init__(session_factory, model)

    def patch_game_params_by_id(self, id: str, schema):
        """
        Updates game parameters by their ID.

        Args:
            id (str): The game parameter ID.
            schema: The schema containing the updated data.

        Returns:
            object: The updated game parameters.

        Raises:
            NotFoundError: If the game parameters are not found.
        """
        with self.session_factory() as session:
            game_params_model = session.query(
                self.model).filter(self.model.id == id).first()

            if game_params_model:
                for key, value in schema.dict(exclude_none=True).items():
                    setattr(game_params_model, key, value)

                session.commit()

                return self.read_by_id(
                    game_params_model.id,
                    not_found_message=f"GameParams not found (id) : "
                    f"{game_params_model.id}",
                )
            raise NotFoundError(f"GameParams not found (id) : {id}")
