from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.logs import Logs
from app.repository.base_repository import BaseRepository


class LogsRepository(BaseRepository):
    """
    Repository class for Logs.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for Logs.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=Logs,
    ) -> None:
        """
        Initializes the LogsRepository with the provided session
          factory and model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for Logs.
        """
        super().__init__(session_factory, model)
