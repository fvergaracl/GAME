from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.model.logs import Logs
from app.repository.base_repository import BaseRepository


class LogsRepository(BaseRepository):
    """
    Repository class for Logs.

    Attributes:
        session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for Logs.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=Logs,
    ) -> None:
        """
        Initializes the LogsRepository with the provided session
          factory and model.

        Args:
            session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
              The session factory.
            model: The SQLAlchemy model class for Logs.
        """
        super().__init__(session_factory, model)
