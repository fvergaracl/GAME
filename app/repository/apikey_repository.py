from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session
from app.model.api_key import ApiKey
from app.repository.base_repository import BaseRepository


class ApiKeyRepository(BaseRepository):
    """
    Repository class for API keys.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for API keys.
    """

    def __init__(
            self,
            session_factory: Callable[..., AbstractContextManager[Session]],
            model=ApiKey) -> None:
        """
        Initializes the ApiKeyRepository with the provided session factory and
          model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for API keys.
        """
        super().__init__(session_factory, model)
    
