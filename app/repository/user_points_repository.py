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

    def get_user_measurement_count(self, userId):
        """
        Retrieves the total number of measurements (or tasks completed) by a specific user.

        Parameters:
        - userId (str): The unique identifier of the user.

        Returns:
        - int: The total number of measurements completed by the user.
        """

        with self.session_factory() as session:
            query = session.query(
                func.count(UserPoints.id).label("measurement_count")
            ).filter(
                UserPoints.userId == userId
            ).one()

            return query.measurement_count

    def get_time_taken_for_last_task(self, userId):
        """
        Retrieves the time taken by a specific user to complete the last task.

        Parameters:
        - userId (str): The unique identifier of the user.

        Returns:
        - float: The time taken to complete the last task, in minutes or other relevant unit.
        """

        with self.session_factory() as session:
            query = session.query(
                func.max(UserPoints.created_at).label("last_task_time")
            ).filter(
                UserPoints.userId == userId
            ).one()

            return query.last_task_time

    def get_individual_calculation(self, userId):
        """
        Calculates and retrieves a specific performance metric for an individual user,
        such as average time taken to complete tasks.

        Parameters:
        - userId (str): The unique identifier of the user.

        Returns:
        - float: The calculated individual performance metric for the user.
        """
        with self.session_factory() as session:
            query = session.query(
                func.avg(UserPoints.points).label("average_points")
            ).filter(
                UserPoints.userId == userId
            ).one()

            return query.average_points

    def get_global_calculation(self):
        """
        Calculates and retrieves a specific global performance metric,
        such as the average time taken to complete tasks across all users.

        Returns:
        - float: The calculated global performance metric.
        """
        with self.session_factory() as session:
            query = session.query(
                func.avg(UserPoints.points).label("average_points")
            ).one()

            return query.average_points
        
    def get_start_time_for_last_task(self, userId):
        """
        Retrieves the start time of the last task completed by a specific user.

        Parameters:
        - userId (str): The unique identifier of the user.

        Returns:
        - datetime: The start time of the last task completed by the user.
        """
        with self.session_factory() as session:
            query = session.query(
                func.min(UserPoints.created_at).label("start_time")
            ).filter(
                UserPoints.userId == userId
            ).one()

            return query.start_time
