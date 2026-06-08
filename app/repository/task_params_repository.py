from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.model.task_params import TasksParams
from app.repository.base_repository import BaseRepository


class TaskParamsRepository(BaseRepository):
    """
    Repository class for task parameters.

    Attributes:
        session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for task parameters.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=TasksParams,
    ) -> None:
        """
        Initializes the TaskParamsRepository with the provided session factory
          and model.

        Args:
            session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
              The session factory.
            model: The SQLAlchemy model class for task parameters.
        """
        super().__init__(session_factory, model)

    async def patch_task_params_by_id(self, id, schema):
        """
        Updates a task parameter row in place by its id.

        Sibling of :meth:`GameParamsRepository.patch_game_params_by_id`,
        used by the task PATCH flow to rewrite a param's ``key``/``value``
        without deleting and recreating the row (so its id is preserved).

        Raises :class:`NotFoundError` if the param does not exist.
        """
        async with self.session_factory() as session:
            stmt = select(self.model).filter(self.model.id == id)
            task_params_model = (await session.execute(stmt)).scalars().first()

            if task_params_model:
                for key, value in schema.model_dump(exclude_none=True).items():
                    setattr(task_params_model, key, value)

                await session.commit()
                target_id = task_params_model.id
            else:
                raise NotFoundError(f"TaskParams not found (id) : {id}")

        return await self.read_by_id(
            target_id,
            not_found_message=f"TaskParams not found (id) : {target_id}",
        )
