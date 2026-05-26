from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.model.user_actions import UserActions
from app.repository.base_repository import BaseRepository
from app.schema.task_schema import AddActionDidByUserInTask


class UserActionsRepository(BaseRepository):
    """
    Repository class for user points.

    Attributes:
        session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for user points.

    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=UserActions,
    ) -> None:
        """
        Initializes the UserPointsRepository with the provided session factory
          and model.

        Args:
            session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
              The session factory.
            model: The SQLAlchemy model class for user points.
        """
        session_factory_userAction = Callable[..., AbstractAsyncContextManager[AsyncSession]]
        model_userAction = UserActions
        self.userAction_repository = BaseRepository(
            session_factory_userAction, model_userAction
        )
        super().__init__(session_factory, model)

    async def add_action_in_task(
        self, user_id: str, task_id: str, action: AddActionDidByUserInTask
    ):
        """
        Add action in task for user.
        """

        async with self.session_factory() as session:
            entity = self.model(
                userId=user_id,
                taskId=task_id,
                typeAction=action.typeAction,
                data=action.data,
                description=action.description,
            )
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity
