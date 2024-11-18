from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.oauth_users import OAuthUsers
from app.repository.base_repository import BaseRepository


class OAuthUsersRepository(BaseRepository):
    """
    Repository class for OAuth users.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for OAuth users.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=OAuthUsers,
    ) -> None:
        """
        Initializes the OAuthUsersRepository with the provided session
          factory and model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for OAuth users.
        """
        super().__init__(session_factory, model)
