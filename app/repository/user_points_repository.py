from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from datetime import timezone
from app.model.tasks import Tasks
from app.model.user_points import UserPoints

from app.model.users import Users
from app.model.games import Games
from app.repository.base_repository import BaseRepository

epoch = func.to_timestamp('1970-01-01', 'YYYY-MM-DD')


class UserPointsRepository(BaseRepository):

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=UserPoints,
    ) -> None:

        session_factory_task = Callable[..., AbstractContextManager[Session]]
        model_task = Tasks
        self.task_repository = BaseRepository(session_factory_task, model_task)
        session_factory_user = Callable[..., AbstractContextManager[Session]]
        model_user = Users
        self.user_repository = BaseRepository(session_factory_user, model_user)

        super().__init__(session_factory, model)

    def create_user_points(
            self, userId, taskId, points, caseName, data, description):
        with self.session_factory() as session:
            user_points = UserPoints(
                userId=userId,
                taskId=taskId,
                points=points,
                caseName=caseName,
                data=data,
                description=description,
            )
            session.add(user_points)
            session.commit()
            return user_points

    def get_all_UserPoints_by_taskId(self, taskId):
        """
        Retrieves all UserPoints for a specific task, sum of points and count
          of times awarded.

        Parameters:
        - taskId (str): The unique identifier of the task.

        Returns:
        - list: A list of tuples containing the externalUserId, sum of points,
          and count of times awarded.
        """
        with self.session_factory() as session:
            query = (
                session.query(
                    Users.externalUserId,
                    func.sum(UserPoints.points).label("points"),
                    func.count(UserPoints.id).label("timesAwarded"),
                )
                .join(UserPoints, Users.id == UserPoints.userId)
                .filter(UserPoints.taskId == taskId)
                .group_by(Users.externalUserId)
                .all()
            )
            return query

    def get_all_UserPoints_by_taskId_with_details(self, taskId):
        # same as get_all_UserPoints_by_taskId but have an array of pointsData
        """

Response body
Download

[
  {
    "externalUserId": "strin43g2",
    "points": 32,
    "timesAwarded": 12,
    "pointsData":[
        {
            "points": 32,
            "caseName": "string",
            "data": {
            "key": "value"
            },
            "description": "string"
        }
    ]
  }
  ]
        """
        with self.session_factory() as session:
            query = (
                session.query(
                    Users.externalUserId,
                    func.sum(UserPoints.points).label("points"),
                    func.count(UserPoints.id).label("timesAwarded"),
                    func.array_agg(
                        func.json_build_object(
                            "points", UserPoints.points,
                            "caseName", UserPoints.caseName,
                            "data", UserPoints.data,
                            "description", UserPoints.description,
                            "created_at", UserPoints.created_at
                        )
                    ).label("pointsData")
                )
                .join(UserPoints, Users.id == UserPoints.userId)
                .filter(UserPoints.taskId == taskId)
                .group_by(Users.externalUserId)
                .all()
            )
            return query

    def get_points_and_users_by_taskId(self, taskId):
        with self.session_factory() as session:
            query = (
                session.query(
                    Users.id.label("userId"),
                    Users.externalUserId,
                    func.sum(UserPoints.points).label("points"),
                )
                .join(UserPoints, Users.id == UserPoints.userId)
                .filter(UserPoints.taskId == taskId)
                .group_by(Users.id)
                .all()
            )
            return query

    def get_users_points_by_externalTaskId_and_externalUserId(
        self, externalTaskId, externalUserId
    ):
        with self.session_factory() as session:
            query = (
                session.query(
                    Tasks.id.label("task_id"),
                    Users.id.label("user_id"),
                    Users.externalUserId.label("externalUserId"),
                    func.sum(UserPoints.points).label("total_points"),
                )
                .join(UserPoints, Tasks.id == UserPoints.taskId)
                .join(Users, UserPoints.userId == Users.id)
                .filter(
                    Tasks.externalTaskId == externalTaskId,
                    Users.externalUserId == externalUserId,
                )
                .group_by(Tasks.id, Users.id)
                .order_by(Users.id, Tasks.id)
                .all()
            )
            return query

    def get_taks_by_userId(self, userId):
        with self.session_factory() as session:
            query = (
                session.query(Tasks)
                .join(UserPoints, Tasks.id == UserPoints.taskId)
                .filter(UserPoints.userId == userId)
                .all()
            )
            return query

    def get_task_and_sum_points_by_userId(self, userId):
        with self.session_factory() as session:
            """
            get points by users separeted by tasks . only with userId
            """
            query = (
                session.query(
                    Tasks.externalTaskId.label("externalTaskId"),
                    func.sum(UserPoints.points).label("points"),
                )
                .join(UserPoints, Tasks.id == UserPoints.taskId)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Users.id == userId)
                .group_by(Tasks.id)
                .order_by(Tasks.id)
                .all()
            )

            return query

    def get_user_measurement_count(self, userId):
        """
        Retrieves the total number of measurements (or tasks completed) by a
        specific user.

        Parameters:
        - userId (str): The unique identifier of the user.

        Returns:
        - int: The total number of measurements completed by the user.
        """

        with self.session_factory() as session:
            query = (
                session.query(func.count(
                    UserPoints.id).label("measurement_count"))
                .filter(UserPoints.userId == userId)
                .one()
            )

            return query.measurement_count

    def get_time_taken_for_last_task(self, userId):
        """
        Retrieves the time taken by a specific user to complete the last task.

        Parameters:
        - userId (str): The unique identifier of the user.

        Returns:
        - float: The time taken to complete the last task, in minutes or other
          relevant unit.
        """
        with self.session_factory() as session:
            query = (
                session.query(
                    func.max(UserPoints.created_at).label("last_task_time"))
                .filter(UserPoints.userId == userId)
                .one()
            )

            return query.last_task_time

    def get_individual_calculation(self, userId):
        """
        Calculates and retrieves a specific performance metric for an
          individual user,
        such as average time taken to complete tasks.

        Parameters:
        - userId (str): The unique identifier of the user.

        Returns:
        - float: The calculated individual performance metric for the user.
        """
        with self.session_factory() as session:
            query = (
                session.query(
                    func.avg(UserPoints.points).label("average_points"))
                .filter(UserPoints.userId == userId)
                .one()
            )

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
            query = (
                session.query(
                    func.min(UserPoints.created_at).label("start_time"))
                .filter(UserPoints.userId == userId)
                .one()
            )

            return query.start_time

    def count_measurements_by_external_task_id(self, external_task_id):
        """
        Retrieves the total number of measurements (or tasks completed) by
         specific external task ID.

        Parameters:
        - external_task_id (str): The unique identifier of the external task.

        Returns:
        - int: The total number of measurements completed for the task.

        """

        with self.session_factory() as session:
            query = (
                session.query(func.count(
                    UserPoints.taskId).label("measurement_count"))
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .filter(Tasks.externalTaskId == external_task_id)
                .one()
            )

            return query.measurement_count

    def get_user_task_measurements_count(self, externalTaskId, externalUserId):
        """
        Retrieves the total number of measurements (or tasks completed) by a
        specific user for a specific task.

        Parameters:
        - externalTaskId (str): The unique identifier of the external task.
        - externalUserId (str): The unique identifier of the user.

        Returns:
        - int: The total number of measurements completed by the user for the
         task.
        """

        with self.session_factory() as session:
            query = (
                session.query(func.count(
                    UserPoints.taskId).label("measurement_count"))
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .one()
            )

            return query.measurement_count

    def get_avg_time_between_tasks_by_user_and_game_task(
            self,
            externalGameId,
            externalTaskId,
            externalUserId
    ):
        """
        Retrieves the average time difference between consecutive tasks completed by
        a specific user for a specific task within a specific game.

        Parameters:
        - externalGameId (str): The unique identifier of the external game.
        - externalTaskId (str): The unique identifier of the external task.
        - externalUserId (str): The unique identifier of the user.

        Returns:
        - float: The average time in seconds between consecutive tasks completed by the user.
                Returns -1 if there are fewer than two tasks completed, thus an average cannot be calculated.
        """

        with self.session_factory() as session:
            timestamps = (
                session.query(UserPoints.created_at)
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Games, Tasks.gameId == Games.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Games.externalGameId == externalGameId)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .order_by(UserPoints.created_at)
                .all()
            )

            if len(timestamps) < 2:
                return -1

            time_diffs = [(timestamps[i + 1][0] - timestamps[i][0]
                           ).total_seconds() for i in range(len(timestamps) - 1)]

            avg_time_diff = sum(time_diffs) / len(time_diffs)

            return avg_time_diff

    def get_avg_time_between_tasks_for_all_users(self, externalGameId, externalTaskId):
        """
        Retrieves the average time difference between consecutive tasks completed by
        all users for a specific task within a specific game.

        Parameters:
        - externalGameId (str): The unique identifier of the external game.
        - externalTaskId (str): The unique identifier of the external task.

        Returns:
        - float: The average time in seconds between consecutive tasks completed by all users
                for the specific task within the specified game. Returns -1 if the average
                cannot be calculated.
        """

        with self.session_factory() as session:
            timestamps = (
                session.query(UserPoints.created_at)
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Games, Tasks.gameId == Games.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Games.externalGameId == externalGameId)
                .order_by(UserPoints.created_at)
                .all()
            )

            if len(timestamps) < 2:
                return -1

            time_diffs = [(
                timestamps[i + 1][0] - timestamps[i][0]).total_seconds()
                for i in range(len(timestamps) - 1)]

            avg_time_diff = sum(time_diffs) / len(time_diffs)

            return avg_time_diff

    def is_task_time_taken_less_than_global_calculation(self, externalTaskId):
        """
        Determines if the time taken for the last task is less than the global
        calculation.

        Parameters:
        - externalTaskId (str): The unique identifier of the external task.

        Returns:
        - bool: True if the time taken for the last task is less than the
          global calculation, False otherwise.
        """
        with self.session_factory() as session:
            query = (
                session.query(UserPoints)
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .order_by(UserPoints.created_at.desc())
                .limit(1)
                .one()
            )

            user_time_taken = query.created_at

            global_time_taken = self.get_global_calculation()

            return user_time_taken < global_time_taken

    def get_last_window_time_diff(self, externalTaskId, externalUserId):
        """
        Retrieves the time difference between the last two measurements by a
        specific user for a specific task.

        Parameters:
        - externalTaskId (str): The unique identifier of the external task.
        - externalUserId (str): The unique identifier of the user.

        Returns:
        - float: The time difference in seconds between the last two
         measurements by the user for the task. If there are fewer than two
         measurements, returns 0.
        """

        with self.session_factory() as session:
            last_two_points = (
                session.query(UserPoints)
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .order_by(UserPoints.created_at.desc())
                .limit(2)
                .all()
            )

            if len(last_two_points) < 2:
                return 0

            time_diff = last_two_points[0].created_at - \
                last_two_points[1].created_at

            return time_diff.total_seconds()

    def get_new_last_window_time_diff(self, externalTaskId, externalUserId, externalGameId):
        """
        Retrieves the last measurement time difference by a specific user for a
        specific task in a specific game and diff with current time.

        Parameters:
        - externalTaskId (str): The unique identifier of the external task.
        - externalUserId (str): The unique identifier of the user.
        - externalGameId (str): The unique identifier of the external game.

        Returns:
        - float: The time difference in seconds between now and the last time the 
        user completed the task for the specific game. If the user has not 
        completed the task before, returns 0.
        """

        with self.session_factory() as session:
            last_point = (
                session.query(UserPoints)
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .join(Games, Tasks.gameId == Games.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .filter(Games.externalGameId == externalGameId)
                .order_by(UserPoints.created_at.desc())
                .first()
            )

            if last_point is None:
                return 0

            current_time = session.query(func.now()).scalar()

            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=timezone.utc)

            if last_point.created_at.tzinfo is None:
                last_created_at = last_point.created_at.replace(
                    tzinfo=timezone.utc)
            else:
                last_created_at = last_point.created_at

            time_diff = current_time - last_created_at

            return time_diff.total_seconds()
