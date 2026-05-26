from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy import delete as sa_delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import configs
from app.core.exceptions import DuplicatedError, NotFoundError
from app.model.game_params import GamesParams
from app.model.games import Games
from app.model.task_params import TasksParams
from app.model.tasks import Tasks
from app.model.user_points import UserPoints
from app.repository.base_repository import BaseRepository
from app.schema.games_schema import BaseGameResult, FindGameResult
from app.util.query_builder import dict_to_sqlalchemy_filter_options


class GameRepository(BaseRepository):
    """
    Repository class for games.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=Games,
        model_tasks=Tasks,
        model_game_params=GamesParams,
        model_tasks_params=TasksParams,
        model_user_points=UserPoints,
    ) -> None:
        self.model_tasks = model_tasks
        self.model_game_params = model_game_params
        self.model_tasks_params = model_tasks_params
        self.model_user_points = model_user_points
        super().__init__(session_factory, model)

    async def get_all_games(
        self,
        schema,
        api_key=None,
        oauth_user_id=None,
        is_admin: bool = False,
    ):
        async with self.session_factory() as session:
            schema_as_dict = schema.model_dump(exclude_none=True)
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

            stmt = select(
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
                    stmt = stmt.options(joinedload(relation))

            stmt = stmt.filter(filter_options).order_by(order_query)
            stmt = stmt.outerjoin(
                GamesParams, Games.id == GamesParams.gameId
            )

            if not is_admin:
                scope_filters = []
                if api_key:
                    scope_filters.append(Games.apiKey_used == api_key)
                if oauth_user_id:
                    scope_filters.append(Games.oauth_user_id == oauth_user_id)

                if not scope_filters:
                    return FindGameResult(
                        items=[],
                        search_options={
                            "page": page,
                            "page_size": page_size,
                            "ordering": ordering,
                            "total_count": 0,
                        },
                    )
                stmt = stmt.filter(or_(*scope_filters))

            if page_size != "all":
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)

            rows = (await session.execute(stmt)).all()

            game_results = {}
            for row in rows:
                game_id = row.id
                if game_id not in game_results:
                    game_results[game_id] = BaseGameResult(
                        gameId=row.id,
                        updated_at=row.updated_at,
                        strategyId=row.strategyId,
                        created_at=row.created_at,
                        externalGameId=row.externalGameId,
                        platform=row.platform,
                        params=[],
                    )
                if row.GamesParams:
                    game_results[game_id].params.append(
                        {
                            "id": row.GamesParams.id,
                            "key": row.GamesParams.key,
                            "value": row.GamesParams.value,
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

    async def get_game_by_id(self, id: str):
        async with self.session_factory() as session:
            game = (
                await session.execute(
                    select(self.model).filter(self.model.id == id)
                )
            ).scalars().first()
            if not game:
                raise NotFoundError(detail=f"Not found id : {id}")
            params = (
                await session.execute(
                    select(self.model_game_params).filter(
                        self.model_game_params.gameId == id
                    )
                )
            ).scalars().all()
            game_params = [
                {"id": p.id, "key": p.key, "value": p.value} for p in params
            ]

            return BaseGameResult(
                gameId=game.id,
                created_at=game.created_at,
                updated_at=game.updated_at,
                externalGameId=game.externalGameId,
                platform=game.platform,
                params=game_params,
            )

    async def patch_game_by_id(self, gameId: str, schema):
        async with self.session_factory() as session:
            game = (
                await session.execute(
                    select(self.model).filter(self.model.id == gameId)
                )
            ).scalars().first()
            if not game:
                raise NotFoundError(detail=f"Not found id : {gameId}")

            for key, value in schema.model_dump(exclude_none=True).items():
                setattr(game, key, value)

            try:
                await session.commit()
                await session.refresh(game)
            except IntegrityError as e:
                raise DuplicatedError(detail=str(e.orig))

        return await self.get_game_by_id(gameId)

    async def delete_game_by_id(self, game_id: str):
        try:
            async with self.session_factory() as session:
                game = (
                    await session.execute(
                        select(self.model).filter(
                            self.model.id == game_id
                        )
                    )
                ).scalars().first()
                if not game:
                    raise NotFoundError(detail=f"Not found id : {game_id}")

                await session.execute(
                    sa_delete(self.model_game_params).where(
                        self.model_game_params.gameId == game_id
                    )
                )

                tasks = (
                    await session.execute(
                        select(self.model_tasks).filter(
                            self.model_tasks.gameId == game_id
                        )
                    )
                ).scalars().all()
                for task in tasks:
                    await session.execute(
                        sa_delete(self.model_tasks_params).where(
                            self.model_tasks_params.taskId == task.id
                        )
                    )
                    await session.execute(
                        sa_delete(self.model_user_points).where(
                            self.model_user_points.taskId == task.id
                        )
                    )

                await session.execute(
                    sa_delete(self.model_tasks).where(
                        self.model_tasks.gameId == game_id
                    )
                )

                await session.delete(game)
                await session.commit()
                return True
        except IntegrityError as e:
            raise DuplicatedError(detail=str(e.orig))
        except NotFoundError:
            raise
        except Exception as e:
            raise NotFoundError(detail=str(e))
