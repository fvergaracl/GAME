from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.user_actions import UserActions
from app.repository.base_repository import BaseRepository
from app.schema.task_schema import AddActionDidByUserInTask


class UserActionsRepository(BaseRepository):
    """
    Repository class for user points.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for user points.

    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=UserActions,
    ) -> None:
        """
        Initializes the UserPointsRepository with the provided session factory
          and model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for user points.
        """
        session_factory_userAction = Callable[..., AbstractContextManager[Session]]
        model_userAction = UserActions
        self.userAction_repository = BaseRepository(
            session_factory_userAction, model_userAction
        )
        super().__init__(session_factory, model)

    def add_action_in_task(
        self, user_id: str, task_id: str, action: AddActionDidByUserInTask
    ):
        """
        Add action in task for user.

        Args:
            user_id (str): The user ID.
            task_id (str): The task ID.
            action (AddActionDidByUserInTask): The action to add.

        Returns:
            object: The added action in task for user.
        """

        with self.session_factory() as session:
            action = self.model(
                userId=user_id,
                taskId=task_id,
                typeAction=action.typeAction,
                data=action.data,
                description=action.description,
            )
            session.add(action)
            session.commit()

            return action
