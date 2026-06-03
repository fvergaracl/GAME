from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy import and_
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, or_, select
from sqlalchemy import update as sa_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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

            # Build the column/scope predicate once and reuse it for both
            # the COUNT and the page query so the two never disagree.
            where_clause = filter_options
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
                where_clause = and_(filter_options, or_(*scope_filters))

            # total_count is the number of matching *games*, independent of
            # the current page — the dashboard needs it to render page
            # controls. Counting here (not len(items)) is what makes real
            # pagination possible.
            total_count = int(
                (
                    await session.execute(
                        select(func.count()).select_from(Games).filter(where_clause)
                    )
                ).scalar()
                or 0
            )

            # Paginate distinct games first. The previous implementation
            # applied LIMIT/OFFSET to a Games⋈GamesParams join, so a game
            # with N params consumed N rows of the page budget and the page
            # held fewer than page_size games. Selecting games on their own
            # keeps the page sized in games; params are fetched separately.
            games_stmt = select(Games).filter(where_clause).order_by(order_query)
            if page_size != "all":
                games_stmt = games_stmt.limit(page_size).offset((page - 1) * page_size)
            game_rows = (await session.execute(games_stmt)).scalars().all()

            params_by_game = {}
            game_ids = [g.id for g in game_rows]
            if game_ids:
                params_rows = (
                    (
                        await session.execute(
                            select(GamesParams).filter(GamesParams.gameId.in_(game_ids))
                        )
                    )
                    .scalars()
                    .all()
                )
                for param in params_rows:
                    params_by_game.setdefault(param.gameId, []).append(
                        {
                            "id": param.id,
                            "key": param.key,
                            "value": param.value,
                        }
                    )

            items = [
                BaseGameResult(
                    gameId=game.id,
                    updated_at=game.updated_at,
                    strategyId=game.strategyId,
                    created_at=game.created_at,
                    externalGameId=game.externalGameId,
                    platform=game.platform,
                    params=params_by_game.get(game.id, []),
                )
                for game in game_rows
            ]

            return FindGameResult(
                items=items,
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
                (await session.execute(select(self.model).filter(self.model.id == id)))
                .scalars()
                .first()
            )
            if not game:
                raise NotFoundError(detail=f"Not found id : {id}")
            params = (
                (
                    await session.execute(
                        select(self.model_game_params).filter(
                            self.model_game_params.gameId == id
                        )
                    )
                )
                .scalars()
                .all()
            )
            game_params = [{"id": p.id, "key": p.key, "value": p.value} for p in params]

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
                (
                    await session.execute(
                        select(self.model).filter(self.model.id == gameId)
                    )
                )
                .scalars()
                .first()
            )
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

    async def list_by_strategy_id(self, strategy_id: str):
        """
        Return all games whose ``strategyId`` matches the given value.

        Used by the Sprint 9 rollback cascade to know which games will be
        reassigned to the rolled-back version (the actual UPDATE goes
        through :meth:`bulk_update_strategy_id`; this helper is exposed
        for audit logging and tests).
        """
        async with self.session_factory() as session:
            stmt = select(self.model).filter(self.model.strategyId == strategy_id)
            return list((await session.execute(stmt)).scalars().all())

    async def list_external_ids(self, ids) -> dict:
        """
        Map internal game ``id`` → ``externalGameId`` for the given ids.

        Used by the Sprint 6 strategy-usage view to render the parent game
        of a task-level assignment by its human-readable external id
        instead of a raw UUID, in a single query rather than N reads.
        """
        unique_ids = list({i for i in ids if i is not None})
        if not unique_ids:
            return {}
        async with self.session_factory() as session:
            stmt = select(self.model.id, self.model.externalGameId).filter(
                self.model.id.in_(unique_ids)
            )
            return {
                row.id: row.externalGameId
                for row in (await session.execute(stmt)).all()
            }

    async def bulk_update_strategy_id(
        self, *, old_strategy_id: str, new_strategy_id: str
    ) -> int:
        """
        Rewrite every game's ``strategyId`` from ``old_strategy_id`` to
        ``new_strategy_id`` in a single UPDATE. Returns the row count so
        the caller can log/audit the cascade.

        Used by the Sprint 9 rollback flow: when a published custom
        strategy is rolled back, the games that pointed at the previous
        UUID get reassigned to the target UUID in one trip so no game is
        left referring to an ARCHIVED row.
        """
        async with self.session_factory() as session:
            result = await session.execute(
                sa_update(self.model)
                .where(self.model.strategyId == old_strategy_id)
                .values(strategyId=new_strategy_id)
            )
            await session.commit()
            return int(result.rowcount or 0)

    async def delete_game_by_id(self, game_id: str):
        try:
            async with self.session_factory() as session:
                game = (
                    (
                        await session.execute(
                            select(self.model).filter(self.model.id == game_id)
                        )
                    )
                    .scalars()
                    .first()
                )
                if not game:
                    raise NotFoundError(detail=f"Not found id : {game_id}")

                await session.execute(
                    sa_delete(self.model_game_params).where(
                        self.model_game_params.gameId == game_id
                    )
                )

                tasks = (
                    (
                        await session.execute(
                            select(self.model_tasks).filter(
                                self.model_tasks.gameId == game_id
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
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
