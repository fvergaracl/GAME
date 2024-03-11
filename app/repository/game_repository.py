from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import configs
from app.core.exceptions import DuplicatedError, NotFoundError
from app.model.game_params import GamesParams
from app.model.tasks import Tasks
from app.model.games import Games
from app.repository.base_repository import BaseRepository
from app.schema.games_schema import BaseGameResult, FindGameResult
from app.util.query_builder import dict_to_sqlalchemy_filter_options


class GameRepository(BaseRepository):
    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=Games,
        model_tasks=Tasks,
        model_game_params=GamesParams,
    ) -> None:
        self.model_tasks = model_tasks
        self.model_game_params = model_game_params
        super().__init__(session_factory, model)

    def get_all_games(self, schema):
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
                self.model, schema_as_dict
            )

            query = session.query(
                Games.id.label("id"),
                Games.created_at.label("created_at"),
                Games.platform.label("platform"),
                Games.endDateTime.label("endDateTime"),
                Games.externalGameId.label("externalGameId"),
                GamesParams,
            )
            eager_loading = schema_as_dict.get("eager", False)
            if eager_loading:
                for relation in getattr(self.model, "eagers", []):
                    query = query.options(joinedload(relation))

            filtered_query = query.filter(filter_options)
            query = filtered_query.order_by(order_query)

            query = query.join(GamesParams, Games.id == GamesParams.gameId)
            query = query.group_by(
                Games.id,
                Games.created_at,
                Games.platform,
                Games.endDateTime,
                Games.externalGameId,
                GamesParams,
            )

            if page_size == "all":
                games = query.all()
            else:
                games = query.limit(page_size).offset(
                    (page - 1) * page_size).all()

            total_count = filtered_query.count()

            game_results = {}
            for game in games:
                game_id = game.id
                if game_id not in game_results:
                    game_results[game_id] = BaseGameResult(
                        id=game.id,
                        created_at=game.created_at,
                        externalGameId=game.externalGameId,
                        platform=game.platform,
                        endDateTime=game.endDateTime,
                        params=[],
                    )
                game_results[game_id].params.append(
                    {
                        "id": game.GamesParams.id,
                        "key": game.GamesParams.paramKey,
                        "value": game.GamesParams.value,
                    }
                )

            return FindGameResult(
                items=list(game_results.values()),
                search_options={
                    "page": page,
                    "page_size": page_size,
                    "ordering": ordering,
                    "total_count": total_count,
                },
            )

    def get_game_by_id(self, id: str):
        with self.session_factory() as session:
            game = session.query(self.model).filter(
                self.model.id == id).first()
            if not game:
                raise NotFoundError(detail=f"Not found id : {id}")
            # buscando los parametros del juego
            params = (
                session.query(self.model_game_params)
                .filter(self.model_game_params.gameId == id)
                .all()
            )
            game_params = []
            for param in params:
                game_params.append(
                    {
                        "id": param.id,
                        "paramKey": param.paramKey,
                        "value": param.value,
                    }
                )

            return BaseGameResult(
                id=game.id,
                created_at=game.created_at,
                updated_at=game.updated_at,
                externalGameId=game.externalGameId,
                platform=game.platform,
                endDateTime=game.endDateTime,
                params=game_params,
            )

    def get_tasks_list_by_game_id(self, id: str):
        with self.session_factory() as session:
            tasks = (
                session.query(self.model_tasks)
                .filter(self.model_tasks.gameId == id)
                .all()
            )
            return tasks

    def patch_game_by_id(self, id: str, schema):
        with self.session_factory() as session:
            game = session.query(self.model).filter(
                self.model.id == id).first()
            if not game:
                raise NotFoundError(detail=f"Not found id : {id}")

            for key, value in schema.dict(exclude_none=True).items():
                setattr(game, key, value)

            try:
                session.commit()
                session.refresh(game)
            except IntegrityError as e:
                raise DuplicatedError(detail=str(e.orig))

            return self.get_game_by_id(id)
