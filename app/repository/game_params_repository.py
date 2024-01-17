from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session
from app.model.game_params import GameParams
from app.repository.base_repository import BaseRepository
from app.schema.games_schema import UpsertGameWithGameParams
from sqlalchemy.orm import Session, joinedload
from app.core.exceptions import NotFoundError


class GameParamsRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]], model=GameParams) -> None:
        super().__init__(session_factory, model)
