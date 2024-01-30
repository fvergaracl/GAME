from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.model.user_points import UserPoints
from app.model.tasks import Tasks
from app.model.users import Users
from app.repository.base_repository import BaseRepository


class UserPointsRepository(BaseRepository):

    def __init__(
        self,
        session_factory: Callable[
            ...,
            AbstractContextManager[Session]],
            model=UserPoints) -> None:

        session_factory_task = Callable[
            ...,
            AbstractContextManager[Session]]
        model_task = Tasks
        self.task_repository = BaseRepository(
            session_factory_task, model_task)
        session_factory_user = Callable[
            ...,
            AbstractContextManager[Session]]
        model_user = Users
        self.user_repository = BaseRepository(
            session_factory_user, model_user)

        super().__init__(session_factory, model)

    def get_all_UserPoints_by_taskId(self, taskId):
        with self.session_factory() as session:
            query = session.query(self.model).filter(
                self.model.taskId == taskId).all()
            return query

    def get_points_and_users_by_taskId(self, taskId):
        with self.session_factory() as session:
            query = session.query(
                Users.id.label("userId"),
                Users.externalUserId,
                # sum userPoints.points
                func.sum(UserPoints.points).label("points")
            ).join(
                UserPoints, Users.id == UserPoints.userId
            ).filter(
                UserPoints.taskId == taskId
            ).group_by(
                Users.id
            ).all()
            return query

    def get_users_points_by_externalTaskId_and_externalUserId(self, externalTaskId, externalUserId):
        with self.session_factory() as session:
            query = session.query(
                Tasks.id.label("task_id"),
                Users.id.label("user_id"),
                Users.externalUserId.label("externalUserId"),
                func.sum(UserPoints.points).label("total_points")
            ).join(
                UserPoints, Tasks.id == UserPoints.taskId
            ).join(
                Users, UserPoints.userId == Users.id
            ).filter(
                Tasks.externalTaskId == externalTaskId,
                Users.externalUserId == externalUserId
            ).group_by(
                Tasks.id,
                Users.id
            ).order_by(
                Users.id,
                Tasks.id
            ).all()
            return query

    def get_task_and_sum_points_by_userId(self, userId):
        with self.session_factory() as session:
            """
            get points by users separeted by tasks . only with userId
            """
            query = session.query(
                Tasks.externalTaskId.label("externalTaskId"),
                func.sum(UserPoints.points).label("points")
            ).join(
                UserPoints, Tasks.id == UserPoints.taskId
            ).join(
                Users, UserPoints.userId == Users.id
            ).filter(
                Users.id == userId
            ).group_by(
                Tasks.id
            ).order_by(
                Tasks.id
            ).all()

            return query
