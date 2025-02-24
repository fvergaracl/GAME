from contextlib import AbstractContextManager
from typing import Callable, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app.model.user_game_config import UserGameConfig
from app.repository.base_repository import BaseRepository


class UserGameConfigRepository(BaseRepository):
    """
    Repository class for managing user-specific game configurations.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for user game configurations.
    """

    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]]
    ) -> None:
        """
        Initializes the UserGameConfigRepository.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
        """
        super().__init__(session_factory, UserGameConfig)
