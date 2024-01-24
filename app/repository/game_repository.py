from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session
from app.model.games import Games
from app.model.game_params import GamesParams
from app.repository.base_repository import BaseRepository
from app.schema.games_schema import (
    UpsertGameWithGameParams,
    FindGameResult,
    BaseGameResult
)
from app.schema.games_params_schema import BaseGameParams
from sqlalchemy.orm import Session, joinedload
from app.util.query_builder import dict_to_sqlalchemy_filter_options
from app.core.config import configs


class GameRepository(BaseRepository):
    def __init__(
            self,
            session_factory: Callable[..., AbstractContextManager[Session]],
            model=Games,
            model_game_params=GamesParams

    ) -> None:
        self.model_game_params = model_game_params
        super().__init__(session_factory, model)

    def get_all_games(self, schema):
        # ACAAAAA
        with self.session_factory() as session:
            schema_as_dict = schema.dict(exclude_none=True)
            ordering = schema_as_dict.get("ordering", configs.ORDERING)
            order_query = (
                getattr(self.model, ordering[1:]).desc()
                if ordering.startswith("-")
                else getattr(self.model, ordering).asc()
            )
            page = schema_as_dict.get("page", configs.PAGE)
            page_size = schema_as_dict.get("page_size", configs.PAGE_SIZE)
            filter_options = dict_to_sqlalchemy_filter_options(
                self.model, schema_as_dict)

            query = session.query(self.model)
            eager_loading = schema_as_dict.get("eager", False)
            if eager_loading:
                for relation in getattr(self.model, "eagers", []):
                    query = query.options(joinedload(relation))

            filtered_query = query.filter(filter_options)
            query = filtered_query.order_by(order_query)

            if page_size == "all":
                games = query.all()
            else:
                games = query.limit(page_size).offset(
                    (page - 1) * page_size).all()

            total_count = filtered_query.count()

            # Transformar los resultados de la consulta en objetos Pydantic
            game_results = [BaseGameResult.from_orm(game) for game in games]

            return FindGameResult(
                items=game_results,
                search_options={
                    "page": page,
                    "page_size": page_size,
                    "ordering": ordering,
                    "total_count": total_count,
                }
            )

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
