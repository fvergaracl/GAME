from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session
from app.model.games import Games
from app.repository.base_repository import BaseRepository
from app.schema.games_schema import UpsertGameWithGameParams
from sqlalchemy.orm import Session, joinedload
from app.core.exceptions import NotFoundError


class GameRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]], model=Games) -> None:
        super().__init__(session_factory, model)

    def update_with_params(self, id: int, schema: UpsertGameWithGameParams, params):
        with self.session_factory() as session:
            session.query(self.model).filter(self.model.id == id).update(
                schema.dict(exclude_none=True))
            query = session.query(self.model).filter(
                self.model.id == id).first()
            if params:
                query.params = []
                session.flush()
                query.params = params
            else:
                query.params = []
            session.commit()
            session.refresh(query)
            return self.read_by_id(id)
