from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import timezone, timedelta
from app.model.tasks import Tasks
from app.model.user_points import UserPoints
from app.model.users import Users
from app.model.games import Games
from app.repository.base_repository import BaseRepository


class UserPointsRepository(BaseRepository):
    """
    Repository class for user points.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for user points.
        task_repository (BaseRepository): Repository instance for tasks.
        user_repository (BaseRepository): Repository instance for users.
    """

    def __init__(
            self,
            session_factory: Callable[..., AbstractContextManager[Session]],
            model=UserPoints) -> None:
        """
        Initializes the UserPointsRepository with the provided session factory
          and model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for user points.
        """
        session_factory_task = Callable[..., AbstractContextManager[Session]]
        model_task = Tasks
        self.task_repository = BaseRepository(session_factory_task, model_task)
        session_factory_user = Callable[..., AbstractContextManager[Session]]
        model_user = Users
        self.user_repository = BaseRepository(session_factory_user, model_user)

        super().__init__(session_factory, model)

    def get_first_user_points_in_external_task_id_by_user_id(
            self,
            externalTaskId,
            externalUserId
    ):
        """
        Retrieves the first user points in an external task by user ID.

        Args:
            externalTaskId (str): The external task ID.
            externalUserId (str): The external user ID.

        Returns:
            UserPoints: The first user points in the task.
        """
        with self.session_factory() as session:
            query = (
                session.query(UserPoints)
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .order_by(UserPoints.created_at)
                .first()
            )
            return query

    def get_all_UserPoints_by_gameId(self, gameId):
        """
        Retrieves all user points associated with a game ID.

        Args:
            gameId (int): The game ID.

        Returns:
            list: A list of user points grouped by task and user.
        """
        with self.session_factory() as session:
            query = (
                session.query(
                    Tasks.externalTaskId.label("externalTaskId"),
                    Users.externalUserId.label("externalUserId"),
                    func.sum(UserPoints.points).label("points"),
                    func.count(UserPoints.id).label("timesAwarded"),
                )
                .join(UserPoints, Tasks.id == UserPoints.taskId)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.gameId == gameId)
                .group_by(Tasks.externalTaskId, Users.externalUserId)
                .all()
            )
            return query

    def get_all_UserPoints_by_taskId(self, taskId):
        """
        Retrieves all user points for a specific task.

        Args:
            taskId (str): The task ID.

        Returns:
            list: A list of user points.
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
        """
        Retrieves all user points for a specific task with details.

        Args:
            taskId (str): The task ID.

        Returns:
            list: A list of user points with detailed information.
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
        """
        Retrieves points and users associated with a task ID.

        Args:
            taskId (int): The task ID.

        Returns:
            list: A list of user points with user information.
        """
        with self.session_factory() as session:
            query = (
                session.query(
                    Users.externalUserId.label("externalUserId"),
                    func.sum(UserPoints.points).label("points"),
                    func.count(UserPoints.id).label("timesAwarded"),
                    func.array_agg(
                        func.json_build_object(
                            "points", UserPoints.points,
                            "caseName", UserPoints.caseName,
                            "created_at", UserPoints.created_at
                        )
                    ).label("pointsData")
                )
                .join(UserPoints, Users.id == UserPoints.userId)
                .filter(UserPoints.taskId == taskId)
                .group_by(Users.id)
                .all()
            )
            return query

    def get_task_by_externalUserId(self, externalUserId):
        """
        Retrieves tasks associated with a user by their external user ID.

        Args:
            externalUserId (str): The external user ID.

        Returns:
            list: A list of tasks.
        """
        with self.session_factory() as session:
            query = (
                session.query(Tasks)
                .join(UserPoints, Tasks.id == UserPoints.taskId)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Users.externalUserId == externalUserId)
                .all()
            )
            return query

    def get_task_and_sum_points_by_userId(self, userId):
        """
        Retrieves tasks and the sum of points for a user by their user ID.

        Args:
            userId (str): The user ID.

        Returns:
            list: A list of tasks with the sum of points.
        """
        with self.session_factory() as session:
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
        Retrieves the total number of measurements (tasks completed) by a
          specific user.

        Args:
            userId (str): The user ID.

        Returns:
            int: The total number of measurements completed by the user.
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
        Retrieves the time taken by a user to complete the last task.

        Args:
            userId (str): The user ID.

        Returns:
            datetime: The time taken to complete the last task.
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
        Calculates and retrieves an individual performance metric for a user.

        Args:
            userId (str): The user ID.

        Returns:
            float: The calculated individual performance metric.
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
        Calculates and retrieves a global performance metric.

        Returns:
            float: The calculated global performance metric.
        """
        with self.session_factory() as session:
            query = session.query(
                func.avg(UserPoints.points).label("average_points")).one()
            return query.average_points

    def get_start_time_for_last_task(self, userId):
        """
        Retrieves the start time of the last task completed by a user.

        Args:
            userId (str): The user ID.

        Returns:
            datetime: The start time of the last task.
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
        Retrieves the total number of measurements by external task ID.

        Args:
            external_task_id (str): The external task ID.

        Returns:
            int: The total number of measurements completed for the task.
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

    def get_user_task_measurements(self, externalTaskId, externalUserId):
        """
        Retrieves measurements for a user and task.

        Args:
            externalTaskId (str): The external task ID.
            externalUserId (str): The external user ID.

        Returns:
            list: A list of measurements for the user and task.
        """
        with self.session_factory() as session:
            query = (
                session.query(UserPoints.created_at.label("timestamp"))
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .order_by(UserPoints.created_at)
                .all()
            )
            return query

    def get_user_task_measurements_count(self, externalTaskId, externalUserId):
        """
        Retrieves the total number of measurements by user and task.

        Args:
            externalTaskId (str): The external task ID.
            externalUserId (str): The external user ID.

        Returns:
            int: The total number of measurements by user and task.
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

    def get_user_task_measurements_count_the_last_seconds(
            self,
            externalTaskId,
            externalUserId,
            seconds
    ):
        """
        Retrieves the total number of measurements by user and task in the last
          n seconds.

        Args:
            externalTaskId (str): The external task ID.
            externalUserId (str): The external user ID.
            seconds (int): The number of seconds to consider.

        Returns:
            int: The total number of measurements by user and task in the last
              n seconds.
        """
        with self.session_factory() as session:
            query = (
                session.query(func.count(
                    UserPoints.taskId).label("measurement_count"))
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .filter(UserPoints.created_at > func.now() - timedelta(seconds=seconds))
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
        Retrieves the average time between tasks for a user and game task.

        Args:
            externalGameId (str): The external game ID.
            externalTaskId (str): The external task ID.
            externalUserId (str): The external user ID.

        Returns:
            float: The average time between tasks.
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

            time_diffs = [(
                timestamps[i + 1][0] - timestamps[i][0]
            ).total_seconds() for i in range(len(timestamps) - 1)]
            avg_time_diff = sum(time_diffs) / len(time_diffs)
            return avg_time_diff

    def get_avg_time_between_tasks_for_all_users(
            self,
            externalGameId,
            externalTaskId
    ):
        """
        Retrieves the average time between tasks for all users for a game task.

        Args:
            externalGameId (str): The external game ID.
            externalTaskId (str): The external task ID.

        Returns:
            float: The average time between tasks for all users.
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
                timestamps[i + 1][0] - timestamps[i][0]
            ).total_seconds() for i in range(len(timestamps) - 1)]
            avg_time_diff = sum(time_diffs) / len(time_diffs)
            return avg_time_diff

    def get_last_window_time_diff(self, externalTaskId, externalUserId):
        """
        Retrieves the time difference between the last two measurements by
          a user for a task.

        Args:
            externalTaskId (str): The external task ID.
            externalUserId (str): The external user ID.

        Returns:
            float: The time difference between the last two measurements.
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

    def get_new_last_window_time_diff(
            self,
            externalTaskId,
            externalUserId,
            externalGameId):
        """
        Retrieves the time difference between the last measurement and current
          time for a user for a task in a game.

        Args:
            externalTaskId (str): The external task ID.
            externalUserId (str): The external user ID.
            externalGameId (str): The external game ID.

        Returns:
            float: The time difference between the last measurement and
              current time.
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
