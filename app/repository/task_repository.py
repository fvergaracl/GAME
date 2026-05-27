from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy import func, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import configs
from app.core.exceptions import NotFoundError
from app.model.tasks import Tasks
from app.repository.base_repository import BaseRepository
from app.util.query_builder import dict_to_sqlalchemy_filter_options


class TaskRepository(BaseRepository):
    """
    Repository class for tasks.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=Tasks,
    ) -> None:
        super().__init__(session_factory, model)

    async def read_by_gameId(self, schema, eager: bool = False):
        """
        Reads tasks filtered by gameId (and any other schema fields).
        """
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
                self.model, schema.model_dump(exclude_none=True)
            )

            stmt = select(self.model).filter(filter_options)
            if eager:
                for eager_rel in getattr(self.model, "eagers", []):
                    stmt = stmt.options(
                        joinedload(getattr(self.model, eager_rel))
                    )

            count_stmt = select(func.count()).select_from(
                select(self.model).filter(filter_options).subquery()
            )
            stmt = stmt.order_by(order_query)
            if page_size != "all":
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)

            items = (await session.execute(stmt)).unique().scalars().all()
            total_count = (await session.execute(count_stmt)).scalar_one()
            return {
                "items": items,
                "search_options": {
                    "page": page,
                    "page_size": page_size,
                    "ordering": ordering,
                    "total_count": total_count,
                },
            }

    async def read_by_gameId_and_externalTaskId(
        self, gameId, externalTaskId: str
    ):
        async with self.session_factory() as session:
            stmt = select(self.model).filter(
                self.model.gameId == gameId,
                self.model.externalTaskId == externalTaskId,
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_points_and_users_by_taskId(self, taskId):
        async with self.session_factory() as session:
            stmt = select(self.model).filter(self.model.id == taskId)
            result = (await session.execute(stmt)).scalars().first()
            if not result:
                raise NotFoundError(detail=f"Task not found by id : {taskId}")
            return result

    async def patch_by_id(self, taskId, fields: dict):
        """
        Apply a small ``fields`` dict to the task identified by
        ``taskId``. Returns the refreshed row. Used by the Sprint 9
        ``PATCH /games/{gameId}/tasks/{taskId}`` flow so the assignments
        admin view can rewrite ``strategyId`` (and ``status``) without a
        full upsert.

        Raises :class:`NotFoundError` if the task does not exist.
        """
        async with self.session_factory() as session:
            stmt = select(self.model).filter(self.model.id == taskId)
            task = (await session.execute(stmt)).scalars().first()
            if not task:
                raise NotFoundError(
                    detail=f"Task not found by id : {taskId}"
                )
            for key, value in fields.items():
                setattr(task, key, value)
            await session.commit()
            await session.refresh(task)
            return task

    async def list_by_strategy_id(self, strategy_id: str):
        """
        Return all tasks whose ``strategyId`` matches the given value.

        Sprint 9 rollback cascade companion to
        :meth:`GameRepository.list_by_strategy_id`.
        """
        async with self.session_factory() as session:
            stmt = select(self.model).filter(
                self.model.strategyId == strategy_id
            )
            return list(
                (await session.execute(stmt)).scalars().all()
            )

    async def bulk_update_strategy_id(
        self, *, old_strategy_id: str, new_strategy_id: str
    ) -> int:
        """
        Rewrite every task's ``strategyId`` from ``old_strategy_id`` to
        ``new_strategy_id`` in a single UPDATE. Returns the row count.

        Sprint 9 rollback cascade companion to
        :meth:`GameRepository.bulk_update_strategy_id`.
        """
        async with self.session_factory() as session:
            result = await session.execute(
                sa_update(self.model)
                .where(self.model.strategyId == old_strategy_id)
                .values(strategyId=new_strategy_id)
            )
            await session.commit()
            return int(result.rowcount or 0)
