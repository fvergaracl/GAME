from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session
from app.model.user_points import UserPoints
from app.repository.base_repository import BaseRepository


class UserPointsRepository(BaseRepository):

    def __init__(
        self,
        session_factory: Callable[
            ...,
            AbstractContextManager[Session]],
            model=UserPoints) -> None:
        super().__init__(session_factory, model)
