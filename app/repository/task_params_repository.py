from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.task_params import TasksParams
from app.repository.base_repository import BaseRepository


class TaskParamsRepository(BaseRepository):
    """
    Repository class for task parameters.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for task parameters.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=TasksParams,
    ) -> None:
        """
        Initializes the TaskParamsRepository with the provided session factory
          and model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for task parameters.
        """
        super().__init__(session_factory, model)
