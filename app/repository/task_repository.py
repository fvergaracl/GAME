from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session
from app.model.tasks import Tasks
from app.repository.base_repository import BaseRepository


class TaskRepository(BaseRepository):

    def __init__(
        self,
        session_factory: Callable[
            ...,
            AbstractContextManager[Session]],
            model=Tasks) -> None:
        super().__init__(session_factory, model)
