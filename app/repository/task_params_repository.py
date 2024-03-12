from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.task_params import TasksParams
from app.repository.base_repository import BaseRepository


class TaskParamsRepository(BaseRepository):
    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=TasksParams,
    ) -> None:
        super().__init__(session_factory, model)
