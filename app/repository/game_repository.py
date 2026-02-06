from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import configs
from app.core.exceptions import DuplicatedError, NotFoundError
from app.model.game_params import GamesParams
from app.model.games import Games
from app.model.task_params import TasksParams
from app.model.tasks import Tasks
from app.model.user_actions import UserActions
from app.model.user_points import UserPoints
from app.repository.base_repository import BaseRepository
from app.schema.games_schema import BaseGameResult, FindGameResult
from app.util.query_builder import dict_to_sqlalchemy_filter_options


class GameRepository(BaseRepository):
    """
    Repository class for games.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for games.
        model_tasks: SQLAlchemy model class for tasks.
        model_game_params: SQLAlchemy model class for game parameters.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=Games,
        model_tasks=Tasks,
        model_game_params=GamesParams,
        model_tasks_params=TasksParams,
        model_user_points=UserPoints,
    ) -> None:
        """
        Initializes the GameRepository with the provided session factory and
          models.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for games.
            model_tasks: The SQLAlchemy model class for tasks.
            model_game_params: The SQLAlchemy model class for game parameters.
        """
        self.model_tasks = model_tasks
        self.model_game_params = model_game_params
        self.model_tasks_params = model_tasks_params
        self.model_user_points = model_user_points
        super().__init__(session_factory, model)

    def get_all_games(self, schema, api_key=None):
        """
        Retrieves all games based on the provided schema.

        Args:
            schema: The schema for filtering the games. Supports filtering by externalGameId, strategyId, platform, etc.

        Returns:
            FindGameResult: A result set containing the games and search options.
        """
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

            # ✅ Esto incluirá el filtro por externalGameId si viene en el schema
            filter_options = dict_to_sqlalchemy_filter_options(
                self.model, schema_as_dict
            )

            query = session.query(
                Games.id.label("id"),
                Games.updated_at.label("updated_at"),
                Games.strategyId.label("strategyId"),
                Games.created_at.label("created_at"),
                Games.platform.label("platform"),
                Games.externalGameId.label("externalGameId"),
                GamesParams,
            )

            eager_loading = schema_as_dict.get("eager", False)
            if eager_loading:
                for relation in getattr(self.model, "eagers", []):
                    query = query.options(joinedload(relation))

            filtered_query = query.filter(filter_options)
            query = filtered_query.order_by(order_query)
            query = query.outerjoin(GamesParams, Games.id == GamesParams.gameId)

            if api_key:
                query = query.filter(Games.apiKey_used == api_key)

            if page_size == "all":
                games = query.all()
            else:
                games = query.limit(page_size).offset((page - 1) * page_size).all()

            game_results = {}
            for game in games:
                game_id = game.id
                if game_id not in game_results:
                    game_results[game_id] = BaseGameResult(
                        gameId=game.id,
                        updated_at=game.updated_at,
                        strategyId=game.strategyId,
                        created_at=game.created_at,
                        externalGameId=game.externalGameId,
                        platform=game.platform,
                        params=[],
                    )
                if game.GamesParams:
                    game_results[game_id].params.append(
                        {
                            "id": game.GamesParams.id,
                            "key": game.GamesParams.key,
                            "value": game.GamesParams.value,
                        }
                    )

            total_count = len(game_results)

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
        """
        Retrieves a game by its ID.

        Args:
            id (str): The game ID.

        Returns:
            BaseGameResult: The game details.
        """
        with self.session_factory() as session:
            game = session.query(self.model).filter(self.model.id == id).first()
            if not game:
                raise NotFoundError(detail=f"Not found id : {id}")
            params = (
                session.query(self.model_game_params)
                .filter(self.model_game_params.gameId == id)
                .all()
            )
            game_params = [
                {"id": param.id, "key": param.key, "value": param.value}
                for param in params
            ]

            return BaseGameResult(
                gameId=game.id,
                created_at=game.created_at,
                updated_at=game.updated_at,
                externalGameId=game.externalGameId,
                platform=game.platform,
                params=game_params,
            )

    def patch_game_by_id(self, gameId: str, schema):
        """
        Updates a game by its ID using the provided schema.

        Args:
            gameId (str): The game ID.
            schema: The schema representing the updated data.

        Returns:
            BaseGameResult: The updated game details.

        Raises:
            NotFoundError: If the game is not found.
            DuplicatedError: If a duplicated error occurs during update.
        """
        with self.session_factory() as session:
            game = session.query(self.model).filter(self.model.id == gameId).first()
            if not game:
                raise NotFoundError(detail=f"Not found id : {gameId}")

            for key, value in schema.dict(exclude_none=True).items():
                setattr(game, key, value)

            try:
                session.commit()
                session.refresh(game)
            except IntegrityError as e:
                raise DuplicatedError(detail=str(e.orig))

            return self.get_game_by_id(gameId)

    def delete_game_by_id(self, game_id: str):
        """
        Deletes a game by its ID , it's delete all games related with gameId in
            games, game_params, tasks and tasks_params.

        Args:
            game_id (str): The game ID.

        Raises:
            NotFoundError: If the game is not found.
        """
        try:
            with self.session_factory() as session:
                game = (
                    session.query(self.model).filter(self.model.id == game_id).first()
                )
                if not game:
                    raise NotFoundError(detail=f"Not found id : {game_id}")

                session.query(self.model_game_params).filter(
                    self.model_game_params.gameId == game_id
                ).delete()

                tasks = (
                    session.query(self.model_tasks)
                    .filter(self.model_tasks.gameId == game_id)
                    .all()
                )
                for task in tasks:
                    session.query(self.model_tasks_params).filter(
                        self.model_tasks_params.taskId == task.id
                    ).delete()

                    session.query(self.model_user_points).filter(
                        self.model_user_points.taskId == task.id
                    ).delete()

                session.query(self.model_tasks).filter(
                    self.model_tasks.gameId == game_id
                ).delete()

                session.delete(game)
                session.commit()
                return True
        except IntegrityError as e:
            raise DuplicatedError(detail=str(e.orig))
        except Exception as e:
            raise NotFoundError(detail=str(e))
