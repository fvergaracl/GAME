from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.strategy import Strategy
from app.repository.base_repository import BaseRepository


class StrategyRepository(BaseRepository):

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=Strategy,
    ) -> None:
        super().__init__(session_factory, model)
