from contextlib import AbstractAsyncContextManager
from datetime import timedelta, timezone
from typing import Callable, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.games import Games
from app.model.tasks import Tasks
from app.model.user_points import UserPoints
from app.model.users import Users
from app.repository.base_repository import BaseRepository


class UserPointsRepository(BaseRepository):
    """
    Async repository class for user points.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=UserPoints,
    ) -> None:
        self.task_repository = BaseRepository(session_factory, Tasks)
        self.user_repository = BaseRepository(session_factory, Users)
        super().__init__(session_factory, model)

    async def get_first_user_points_in_external_task_id_by_user_id(
        self, externalTaskId, externalUserId
    ):
        """
        Return the earliest points row for a user on a given external task.

        Args:
            externalTaskId: External identifier of the task.
            externalUserId: External identifier of the user.

        Returns:
            UserPoints | None: The oldest matching points row, or ``None``.
        """
        async with self.session_factory() as session:
            stmt = (
                select(UserPoints)
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .order_by(UserPoints.created_at)
            )
            return (await session.execute(stmt)).scalars().first()

    async def read_by_user_task_and_idempotency(
        self,
        user_id,
        task_id,
        idempotency_key: str,
        session: Optional[AsyncSession] = None,
    ):
        """
        Returns a previously persisted user-points row for the same
        (userId, taskId, idempotencyKey), if it exists.
        """
        if not idempotency_key:
            return None
        if session is None:
            async with self.session_factory() as managed_session:
                return await self.read_by_user_task_and_idempotency(
                    user_id=user_id,
                    task_id=task_id,
                    idempotency_key=idempotency_key,
                    session=managed_session,
                )

        stmt = select(self.model).filter(
            self.model.userId == user_id,
            self.model.taskId == task_id,
            self.model.idempotencyKey == idempotency_key,
        )
        return (await session.execute(stmt)).scalars().first()

    async def get_all_UserPoints_by_gameId(self, gameId):
        """
        Aggregate points per (task, user) for every task in a game.

        Args:
            gameId: Internal game identifier.

        Returns:
            list: Rows of ``(externalTaskId, externalUserId, points,
            timesAwarded)`` where ``points`` is the summed total and
            ``timesAwarded`` the number of awards.
        """
        async with self.session_factory() as session:
            stmt = (
                select(
                    Tasks.externalTaskId.label("externalTaskId"),
                    Users.externalUserId.label("externalUserId"),
                    func.sum(UserPoints.points).label("points"),
                    func.count(UserPoints.id).label("timesAwarded"),
                )
                .join(UserPoints, Tasks.id == UserPoints.taskId)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.gameId == gameId)
                .group_by(Tasks.externalTaskId, Users.externalUserId)
            )
            return (await session.execute(stmt)).all()

    async def get_all_UserPoints_by_taskId(self, taskId):
        """
        Aggregate points per user for a single task.

        Args:
            taskId: Internal task identifier.

        Returns:
            list: Rows of ``(externalUserId, points, timesAwarded)`` with the
            summed points and award count per user.
        """
        async with self.session_factory() as session:
            stmt = (
                select(
                    Users.externalUserId,
                    func.sum(UserPoints.points).label("points"),
                    func.count(UserPoints.id).label("timesAwarded"),
                )
                .join(UserPoints, Users.id == UserPoints.userId)
                .filter(UserPoints.taskId == taskId)
                .group_by(Users.externalUserId)
            )
            return (await session.execute(stmt)).all()

    async def get_all_UserPoints_by_taskId_with_details(self, taskId):
        """
        Aggregate points per user for a task, including per-award detail.

        Like :meth:`get_all_UserPoints_by_taskId` but also returns a
        ``pointsData`` array aggregating each award's ``points``, ``caseName``,
        ``data``, ``description`` and ``created_at``.

        Args:
            taskId: Internal task identifier.

        Returns:
            list: Rows of ``(externalUserId, points, timesAwarded,
            pointsData)``.
        """
        async with self.session_factory() as session:
            stmt = (
                select(
                    Users.externalUserId,
                    func.sum(UserPoints.points).label("points"),
                    func.count(UserPoints.id).label("timesAwarded"),
                    func.array_agg(
                        func.json_build_object(
                            "points",
                            UserPoints.points,
                            "caseName",
                            UserPoints.caseName,
                            "data",
                            UserPoints.data,
                            "description",
                            UserPoints.description,
                            "created_at",
                            UserPoints.created_at,
                        )
                    ).label("pointsData"),
                )
                .join(UserPoints, Users.id == UserPoints.userId)
                .filter(UserPoints.taskId == taskId)
                .group_by(Users.externalUserId)
            )
            return (await session.execute(stmt)).all()

    async def get_points_and_users_by_taskId(self, taskId):
        """
        Aggregate points per user for a task with a compact award breakdown.

        Args:
            taskId: Internal task identifier.

        Returns:
            list: Rows of ``(externalUserId, points, timesAwarded,
            pointsData)`` where ``pointsData`` aggregates each award's
            ``points``, ``caseName`` and ``created_at``.
        """
        async with self.session_factory() as session:
            stmt = (
                select(
                    Users.externalUserId.label("externalUserId"),
                    func.sum(UserPoints.points).label("points"),
                    func.count(UserPoints.id).label("timesAwarded"),
                    func.array_agg(
                        func.json_build_object(
                            "points",
                            UserPoints.points,
                            "caseName",
                            UserPoints.caseName,
                            "created_at",
                            UserPoints.created_at,
                        )
                    ).label("pointsData"),
                )
                .join(UserPoints, Users.id == UserPoints.userId)
                .filter(UserPoints.taskId == taskId)
                .group_by(Users.id)
            )
            return (await session.execute(stmt)).all()

    async def get_points_and_users_by_taskIds(self, task_ids):
        """
        Batched form of :meth:`get_points_and_users_by_taskId`.

        Aggregates points per (task, user) for **every** task in ``task_ids``
        in a single ``taskId IN (...)`` query instead of one round-trip per
        task, eliminating the N+1 the per-game readers used to incur. Each row
        carries ``taskId`` so callers can group the result back per task. The
        leading column of ``ix_user_points_task_user_created`` serves the
        ``IN`` filter and the group-by.

        Args:
            task_ids: Iterable of internal task identifiers.

        Returns:
            list: Rows of ``(taskId, externalUserId, points, timesAwarded,
            pointsData)`` -- the same per (task, user) shape as the single-task
            method, plus ``taskId``. Empty list when ``task_ids`` is empty.
        """
        if not task_ids:
            return []
        async with self.session_factory() as session:
            stmt = (
                select(
                    UserPoints.taskId.label("taskId"),
                    Users.externalUserId.label("externalUserId"),
                    func.sum(UserPoints.points).label("points"),
                    func.count(UserPoints.id).label("timesAwarded"),
                    func.array_agg(
                        func.json_build_object(
                            "points",
                            UserPoints.points,
                            "caseName",
                            UserPoints.caseName,
                            "created_at",
                            UserPoints.created_at,
                        )
                    ).label("pointsData"),
                )
                .join(UserPoints, Users.id == UserPoints.userId)
                .filter(UserPoints.taskId.in_(task_ids))
                .group_by(UserPoints.taskId, Users.id)
            )
            return (await session.execute(stmt)).all()

    async def get_task_by_externalUserId(self, externalUserId):
        """
        Return all tasks a user has earned points on.

        Args:
            externalUserId: External identifier of the user.

        Returns:
            list[Tasks]: Distinct tasks linked to the user's points rows.
        """
        async with self.session_factory() as session:
            stmt = (
                select(Tasks)
                .join(UserPoints, Tasks.id == UserPoints.taskId)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Users.externalUserId == externalUserId)
            )
            return (await session.execute(stmt)).scalars().all()

    async def get_task_and_sum_points_by_userId(self, userId):
        """
        Sum a user's points grouped by task.

        Args:
            userId: Internal user identifier.

        Returns:
            list: Rows of ``(externalTaskId, points)`` with the total points
            the user earned on each task.
        """
        async with self.session_factory() as session:
            stmt = (
                select(
                    Tasks.externalTaskId.label("externalTaskId"),
                    func.sum(UserPoints.points).label("points"),
                )
                .join(UserPoints, Tasks.id == UserPoints.taskId)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Users.id == userId)
                .group_by(Tasks.id)
                .order_by(Tasks.id)
            )
            return (await session.execute(stmt)).all()

    async def get_user_measurement_count(self, userId):
        """
        Count how many points rows (measurements) a user has.

        Args:
            userId: Internal user identifier.

        Returns:
            int: Number of points rows for the user.
        """
        async with self.session_factory() as session:
            stmt = select(func.count(UserPoints.id).label("measurement_count")).filter(
                UserPoints.userId == userId
            )
            result = (await session.execute(stmt)).one()
            return result.measurement_count

    async def get_time_taken_for_last_task(self, userId):
        """
        Return the timestamp of a user's most recent points row.

        Args:
            userId: Internal user identifier.

        Returns:
            datetime | None: The maximum ``created_at`` for the user, or
            ``None`` if they have no rows.
        """
        async with self.session_factory() as session:
            stmt = select(
                func.max(UserPoints.created_at).label("last_task_time")
            ).filter(UserPoints.userId == userId)
            result = (await session.execute(stmt)).one()
            return result.last_task_time

    async def get_individual_calculation(self, userId):
        """
        Return a user's average points per award.

        Args:
            userId: Internal user identifier.

        Returns:
            float | None: Mean of ``points`` across the user's rows, or
            ``None`` if they have none.
        """
        async with self.session_factory() as session:
            stmt = select(func.avg(UserPoints.points).label("average_points")).filter(
                UserPoints.userId == userId
            )
            result = (await session.execute(stmt)).one()
            return result.average_points

    async def get_global_calculation(self):
        """
        Return the average points per award across all users.

        Returns:
            float | None: Mean of ``points`` over every points row, or
            ``None`` if the table is empty.
        """
        async with self.session_factory() as session:
            stmt = select(func.avg(UserPoints.points).label("average_points"))
            result = (await session.execute(stmt)).one()
            return result.average_points

    async def get_start_time_for_last_task(self, userId):
        """
        Return the timestamp of a user's earliest points row.

        Args:
            userId: Internal user identifier.

        Returns:
            datetime | None: The minimum ``created_at`` for the user, or
            ``None`` if they have no rows.
        """
        async with self.session_factory() as session:
            stmt = select(func.min(UserPoints.created_at).label("start_time")).filter(
                UserPoints.userId == userId
            )
            result = (await session.execute(stmt)).one()
            return result.start_time

    async def count_measurements_by_external_task_id(self, external_task_id):
        """
        Count all points rows recorded for an external task.

        Args:
            external_task_id: External identifier of the task.

        Returns:
            int: Number of points rows linked to the task.
        """
        async with self.session_factory() as session:
            stmt = (
                select(func.count(UserPoints.taskId).label("measurement_count"))
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .filter(Tasks.externalTaskId == external_task_id)
            )
            result = (await session.execute(stmt)).one()
            return result.measurement_count

    async def get_user_task_measurements(self, externalTaskId, externalUserId):
        """
        Return the ordered timestamps of a user's awards on a task.

        Args:
            externalTaskId: External identifier of the task.
            externalUserId: External identifier of the user.

        Returns:
            list: Rows of ``(timestamp,)`` ordered chronologically.
        """
        async with self.session_factory() as session:
            stmt = (
                select(UserPoints.created_at.label("timestamp"))
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .order_by(UserPoints.created_at)
            )
            return (await session.execute(stmt)).all()

    async def get_user_task_measurements_count(self, externalTaskId, externalUserId):
        """
        Count a user's awards on a given external task.

        Args:
            externalTaskId: External identifier of the task.
            externalUserId: External identifier of the user.

        Returns:
            int: Number of points rows for the user on that task.
        """
        async with self.session_factory() as session:
            stmt = (
                select(func.count(UserPoints.taskId).label("measurement_count"))
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
            )
            result = (await session.execute(stmt)).one()
            return result.measurement_count

    async def get_user_task_measurements_count_the_last_seconds(
        self, externalTaskId, externalUserId, seconds
    ):
        """
        Count a user's recent awards on a task within a time window.

        Args:
            externalTaskId: External identifier of the task.
            externalUserId: External identifier of the user.
            seconds: Length of the look-back window, in seconds.

        Returns:
            int: Number of points rows created within the last ``seconds``.
        """
        async with self.session_factory() as session:
            stmt = (
                select(func.count(UserPoints.taskId).label("measurement_count"))
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .filter(UserPoints.created_at > func.now() - timedelta(seconds=seconds))
            )
            result = (await session.execute(stmt)).one()
            return result.measurement_count

    async def get_avg_time_between_tasks_by_user_and_game_task(
        self, externalGameId, externalTaskId, externalUserId
    ):
        """
        Average the gap between a user's consecutive awards on a task.

        Args:
            externalGameId: External identifier of the game.
            externalTaskId: External identifier of the task.
            externalUserId: External identifier of the user.

        Returns:
            float: Mean seconds between consecutive awards, or ``-1`` when the
            user has fewer than two awards.
        """
        async with self.session_factory() as session:
            stmt = (
                select(UserPoints.created_at)
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Games, Tasks.gameId == Games.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Games.externalGameId == externalGameId)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .order_by(UserPoints.created_at)
            )
            timestamps = (await session.execute(stmt)).all()

            if len(timestamps) < 2:
                return -1

            time_diffs = [
                (timestamps[i + 1][0] - timestamps[i][0]).total_seconds()
                for i in range(len(timestamps) - 1)
            ]
            return sum(time_diffs) / len(time_diffs)

    async def get_avg_time_between_tasks_for_all_users(
        self, externalGameId, externalTaskId
    ):
        """
        Average the gap between consecutive awards on a task across all users.

        Args:
            externalGameId: External identifier of the game.
            externalTaskId: External identifier of the task.

        Returns:
            float: Mean seconds between consecutive awards, or ``-1`` when
            fewer than two awards exist.
        """
        async with self.session_factory() as session:
            stmt = (
                select(UserPoints.created_at)
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Games, Tasks.gameId == Games.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Games.externalGameId == externalGameId)
                .order_by(UserPoints.created_at)
            )
            timestamps = (await session.execute(stmt)).all()

            if len(timestamps) < 2:
                return -1

            time_diffs = [
                (timestamps[i + 1][0] - timestamps[i][0]).total_seconds()
                for i in range(len(timestamps) - 1)
            ]
            return sum(time_diffs) / len(time_diffs)

    async def get_last_window_time_diff(self, externalTaskId, externalUserId):
        """
        Return seconds between a user's two most recent awards on a task.

        Args:
            externalTaskId: External identifier of the task.
            externalUserId: External identifier of the user.

        Returns:
            float: Seconds between the last two awards, or ``0`` when the user
            has fewer than two.
        """
        async with self.session_factory() as session:
            stmt = (
                select(UserPoints)
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .order_by(UserPoints.created_at.desc())
                .limit(2)
            )
            last_two_points = (await session.execute(stmt)).scalars().all()

            if len(last_two_points) < 2:
                return 0

            time_diff = last_two_points[0].created_at - last_two_points[1].created_at
            return time_diff.total_seconds()

    async def get_new_last_window_time_diff(
        self, externalTaskId, externalUserId, externalGameId
    ):
        """
        Return seconds elapsed since a user's most recent award on a task.

        Measures the gap between *now* and the user's latest award (scoped by
        game and task), normalizing both timestamps to UTC.

        Args:
            externalTaskId: External identifier of the task.
            externalUserId: External identifier of the user.
            externalGameId: External identifier of the game.

        Returns:
            float: Seconds since the last award, or ``0`` if the user has none.
        """
        async with self.session_factory() as session:
            stmt = (
                select(UserPoints)
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .join(Games, Tasks.gameId == Games.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .filter(Games.externalGameId == externalGameId)
                .order_by(UserPoints.created_at.desc())
            )
            last_point = (await session.execute(stmt)).scalars().first()

            if last_point is None:
                return 0

            current_time = (await session.execute(select(func.now()))).scalar()

            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=timezone.utc)

            if last_point.created_at.tzinfo is None:
                last_created_at = last_point.created_at.replace(tzinfo=timezone.utc)
            else:
                last_created_at = last_point.created_at

            time_diff = current_time - last_created_at
            return time_diff.total_seconds()

    async def count_personal_records_by_external_game_id(
        self, externalGameId, externalUserId
    ):
        """
        Count a user's total awards across a game.

        Args:
            externalGameId: External identifier of the game.
            externalUserId: External identifier of the user.

        Returns:
            int: Number of points rows for the user within the game.
        """
        async with self.session_factory() as session:
            stmt = (
                select(func.count(UserPoints.id).label("record_count"))
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Games, Tasks.gameId == Games.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Games.externalGameId == externalGameId)
                .filter(Users.externalUserId == externalUserId)
            )
            result = (await session.execute(stmt)).one()
            return result.record_count

    async def user_has_record_before_in_externalTaskId_last_min(
        self, externalTaskId, externalUserId, minutes
    ):
        """
        Check whether a user earned points on a task within recent minutes.

        Args:
            externalTaskId: External identifier of the task.
            externalUserId: External identifier of the user.
            minutes: Length of the look-back window, in minutes.

        Returns:
            bool: ``True`` if at least one award exists within the window.
        """
        async with self.session_factory() as session:
            stmt = (
                select(func.count(UserPoints.id))
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(Users.externalUserId == externalUserId)
                .filter(UserPoints.created_at > func.now() - timedelta(minutes=minutes))
            )
            count = (await session.execute(stmt)).scalar_one()
            return count > 0

    async def get_global_avg_by_external_game_id(self, externalGameId):
        """
        Average the ``data["minutes"]`` measurement across a whole game.

        Considers only rows with a positive ``minutes`` value in their JSON
        ``data`` payload.

        Args:
            externalGameId: External identifier of the game.

        Returns:
            float: Mean ``minutes`` over all users, or ``-1`` when no
            qualifying rows exist.
        """
        async with self.session_factory() as session:
            stmt = (
                select(
                    func.avg(UserPoints.data["minutes"].as_float()).label(
                        "average_minutes"
                    )
                )
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Games, Tasks.gameId == Games.id)
                .filter(Games.externalGameId == externalGameId)
                .filter(UserPoints.data["minutes"].as_float() > 0)
            )
            result = (await session.execute(stmt)).one()
            return result.average_minutes if result.average_minutes is not None else -1

    async def get_personal_avg_by_external_game_id(
        self, externalGameId, externalUserId
    ):
        """
        Average one user's ``data["minutes"]`` measurement across a game.

        Considers only rows with a positive ``minutes`` value in their JSON
        ``data`` payload.

        Args:
            externalGameId: External identifier of the game.
            externalUserId: External identifier of the user.

        Returns:
            float: Mean ``minutes`` for the user, or ``-1`` when no qualifying
            rows exist.
        """
        async with self.session_factory() as session:
            stmt = (
                select(
                    func.avg(UserPoints.data["minutes"].as_float()).label(
                        "average_minutes"
                    )
                )
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .join(Games, Tasks.gameId == Games.id)
                .join(Users, UserPoints.userId == Users.id)
                .filter(Games.externalGameId == externalGameId)
                .filter(Users.externalUserId == externalUserId)
                .filter(UserPoints.data["minutes"].as_float() > 0)
            )
            result = (await session.execute(stmt)).one()
            return result.average_minutes if result.average_minutes is not None else -1

    async def get_points_of_simulated_task(
        self, externalTaskId: str, simulationHash: str
    ):
        """
        Return points rows produced by a specific strategy simulation run.

        Matches rows whose JSON ``data`` carries the given ``simulationHash``.

        Args:
            externalTaskId (str): External identifier of the task.
            simulationHash (str): Hash identifying the simulation run.

        Returns:
            list[UserPoints]: Points rows belonging to that simulation.
        """
        async with self.session_factory() as session:
            stmt = (
                select(UserPoints)
                .join(Tasks, UserPoints.taskId == Tasks.id)
                .filter(Tasks.externalTaskId == externalTaskId)
                .filter(UserPoints.data["simulationHash"].astext == simulationHash)
            )
            return (await session.execute(stmt)).scalars().all()

    async def get_all_point_of_tasks_list(self, task_list, withData=False):
        """
        Retrieves all points associated with a list of task IDs.

        Note: previously used ``yield_per`` to stream results -- under async
        we materialize fully. For very large task_list batches consider
        streaming via ``stream_scalars`` (caller decides).
        """
        async with self.session_factory() as session:
            stmt = select(UserPoints).filter(UserPoints.taskId.in_(task_list))

            if not withData:
                stmt = stmt.with_only_columns(
                    UserPoints.id,
                    UserPoints.created_at,
                    UserPoints.updated_at,
                    UserPoints.points,
                    UserPoints.caseName,
                    UserPoints.description,
                    UserPoints.userId,
                    UserPoints.taskId,
                    UserPoints.apiKey_used,
                )
                return (await session.execute(stmt)).all()

            return (await session.execute(stmt)).scalars().all()

    async def get_last_task_by_userId(self, userId):
        """
        Return a user's most recent points row.

        Args:
            userId: Internal user identifier.

        Returns:
            UserPoints | None: The latest award by ``created_at``, or ``None``.
        """
        async with self.session_factory() as session:
            stmt = (
                select(UserPoints)
                .filter(UserPoints.userId == userId)
                .order_by(UserPoints.created_at.desc())
            )
            return (await session.execute(stmt)).scalars().first()
