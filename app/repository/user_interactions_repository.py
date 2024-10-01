from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.user_interactions import UserInteractions
from app.repository.base_repository import BaseRepository


class UserInteractionsRepository(BaseRepository):
    """
    Repository class for User interactions.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for User interactions.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=UserInteractions,
    ) -> None:
        """
        Initializes the UserInteractionsRepository with the provided session
          factory and model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for User interactions.
        """
        super().__init__(session_factory, model)
