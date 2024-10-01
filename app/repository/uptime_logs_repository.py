from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.uptime_logs import UptimeLogs
from app.repository.base_repository import BaseRepository


class UptimeLogsRepository(BaseRepository):
    """
    Repository class for Uptime Logs.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for Uptime Logs.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=UptimeLogs,
    ) -> None:
        """
        Initializes the UptimeLogsRepository with the provided session factory
          and model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for Uptime Logs.
        """
        super().__init__(session_factory, model)
