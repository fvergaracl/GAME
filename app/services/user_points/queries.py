"""Read-only points queries.

Aggregations and lookups over ``user_points`` for games, tasks and users.
These methods never mutate state; the write path lives in
:mod:`app.services.user_points.assignment`.
"""

import asyncio
from typing import Any
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.schema.games_schema import ListTasksWithUsers
from app.schema.task_schema import BaseUserFirstAction, TasksWithUsers
from app.schema.user_points_schema import (AllPointsByGame, GameDetail,
                                           PointsAssignedToUser,
                                           PointsAssignedToUserDetails,
                                           ResponseGetPointsByGame,
                                           ResponseGetPointsByTask,
                                           ResponsePointsByExternalUserId, TaskDetail,
                                           TaskPointsByGame, UserGamePoints)
from app.services.game_access import get_authorized_game, get_authorized_user
from app.services.user_points._base import FANOUT_LIMIT, UserPointsContext


class PointsQueryMixin(UserPointsContext):
    async def query_user_points(self, schema) -> Any:
        """
        Run a filtered, paginated query over the ``user_points`` table.

        Args:
            schema: Search schema with filters and ordering/pagination.

        Returns:
            Any: Items plus search metadata, as returned by the repository.
        """
        return await self.user_points_repository.read_by_options(schema)

    async def get_users_by_gameId(
        self,
        gameId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> ListTasksWithUsers:
        """
        List a game's tasks and, per task, the users who earned points.

        For each user the response includes their first action timestamp on
        that task.

        Args:
            gameId: Internal game identifier.
            api_key (str): Caller's API key, used when ``enforce_scope``.
            oauth_user_id (str): Caller's OAuth subject, used when scoping.
            is_admin (bool): Whether the caller has the admin role.
            enforce_scope (bool): When ``True``, verify the caller may access
                the game before returning data.

        Returns:
            ListTasksWithUsers: Tasks each paired with their participating
            users.

        Raises:
            NotFoundError: If the game or its tasks do not exist.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_column(
                "id", gameId, not_found_raise_exception=False
            )
        if not game:
            raise NotFoundError(detail=f"Game not found by gameId: {game}")
        tasks = await self.task_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        if not tasks:
            raise NotFoundError(detail=f"Tasks not found by gameId: {game.id}")
        response = []
        all_tasks = []
        for task in tasks:
            all_externalUserId = []
            points = await self.user_points_repository.get_points_and_users_by_taskId(
                task.id
            )

            externalTaskId = task.externalTaskId
            if points:
                for point in points:

                    externalUserId = point.externalUserId
                    user = await self.users_repository.read_by_column(
                        "externalUserId", externalUserId, not_found_raise_exception=True
                    )
                    if not user:
                        raise NotFoundError(
                            detail=f"User not found by userId: {point.userId}. Please try again later or contact support"  # noqa
                        )
                    first_user_point = await self.user_points_repository.get_first_user_points_in_external_task_id_by_user_id(
                        externalTaskId, externalUserId
                    )
                    all_externalUserId.append(
                        BaseUserFirstAction(
                            externalUserId=user.externalUserId,
                            created_at=str(user.created_at),
                            firstAction=str(first_user_point.created_at),
                        )
                    )
            all_tasks = {"externalTaskId": externalTaskId, "users": all_externalUserId}
            response.append(TasksWithUsers(**all_tasks))
        return ListTasksWithUsers(gameId=gameId, tasks=response)

    async def get_points_by_user_list(
        self,
        users_list,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> list[UserGamePoints]:
        """
        Fetch per-game point totals for a list of users, concurrently.

        Fans out one :meth:`get_all_points_by_externalUserId` call per user,
        bounded by a concurrency semaphore.

        Args:
            users_list: External user identifiers to look up.
            api_key (str): Caller's API key, used when ``enforce_scope``.
            oauth_user_id (str): Caller's OAuth subject, used when scoping.
            is_admin (bool): Whether the caller has the admin role.
            enforce_scope (bool): When ``True``, enforce per-user access checks.

        Returns:
            list[UserGamePoints]: One aggregate result per requested user.
        """
        semaphore = asyncio.Semaphore(FANOUT_LIMIT)

        async def _fetch(user) -> UserGamePoints:
            """Fetch one user's totals under the shared concurrency semaphore."""
            async with semaphore:
                return await self.get_all_points_by_externalUserId(
                    user,
                    api_key=api_key,
                    oauth_user_id=oauth_user_id,
                    is_admin=is_admin,
                    enforce_scope=enforce_scope,
                )

        return list(await asyncio.gather(*[_fetch(u) for u in users_list]))

    async def get_points_by_externalUserId(
        self,
        externalUserId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> list[AllPointsByGame]:
        """
        Return a user's points across every game they participate in.

        Resolves the user, finds the games behind their points rows, and
        aggregates each game's detailed points concurrently.

        Args:
            externalUserId: External identifier of the user.
            api_key (str): Caller's API key, used when ``enforce_scope``.
            oauth_user_id (str): Caller's OAuth subject, used when scoping.
            is_admin (bool): Whether the caller has the admin role.
            enforce_scope (bool): When ``True``, verify access to the user.

        Returns:
            list[AllPointsByGame]: Detailed points grouped per game.

        Raises:
            NotFoundError: If the user does not exist.
        """
        if enforce_scope:
            user = await get_authorized_user(
                self.users_repository,
                externalUserId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            user = await self.users_repository.read_by_column(
                "externalUserId", externalUserId, not_found_raise_exception=True
            )
        if not user:
            raise NotFoundError(
                detail=f"User not found by externalUserId: {externalUserId}"
            )

        tasks_of_users = await self.user_points_repository.get_task_by_externalUserId(
            externalUserId
        )

        semaphore = asyncio.Semaphore(FANOUT_LIMIT)

        async def _fetch(task) -> AllPointsByGame:
            """Resolve a task's game and fetch its detailed points, bounded."""
            async with semaphore:
                game = await self.game_repository.read_by_column(
                    "id", task.gameId, not_found_raise_exception=True
                )
                return await self.get_points_by_gameId_with_details(
                    game.id,
                    api_key=api_key,
                    oauth_user_id=oauth_user_id,
                    is_admin=is_admin,
                    enforce_scope=enforce_scope,
                )

        response = list(
            await asyncio.gather(*[_fetch(task) for task in tasks_of_users])
        )

        new_response = []
        for game in response:
            for task in game.task:
                for point in task.points:
                    if point.externalUserId == externalUserId:
                        new_response.append(
                            AllPointsByGame(
                                externalGameId=game.externalGameId,
                                created_at=game.created_at,
                                task=[
                                    TaskPointsByGame(
                                        externalTaskId=task.externalTaskId,
                                        points=[
                                            PointsAssignedToUser(
                                                externalUserId=point.externalUserId,
                                                points=point.points,
                                                timesAwarded=point.timesAwarded,
                                                pointsData=point.pointsData,
                                            )
                                        ],
                                    )
                                ],
                            )
                        )
        return new_response

    async def get_points_by_gameId(
        self,
        gameId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> AllPointsByGame:
        """
        Aggregate all points awarded within a game.

        Args:
            gameId: Internal game identifier.
            api_key (str): Caller's API key, used when ``enforce_scope``.
            oauth_user_id (str): Caller's OAuth subject, used when scoping.
            is_admin (bool): Whether the caller has the admin role.
            enforce_scope (bool): When ``True``, verify access to the game.

        Returns:
            AllPointsByGame: The game's aggregated points.

        Raises:
            NotFoundError: If the game does not exist.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_column(
                "id", gameId, not_found_message=f"Game with gameId: {gameId} not found"
            )
        tasks = await self.task_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )

        if not tasks:
            raise NotFoundError(detail=f"Tasks not found by gameId: {game.id}")
        game_points = []
        for task in tasks:
            user_points = []
            points = await self.user_points_repository.get_points_and_users_by_taskId(
                task.id
            )
            if points:

                for point in points:
                    points_of_user = PointsAssignedToUser(
                        externalUserId=point.externalUserId,
                        points=point.points,
                        timesAwarded=point.timesAwarded,
                    )
                    user_points.append(points_of_user)

            task_points = TaskPointsByGame(
                externalTaskId=task.externalTaskId, points=user_points
            )
            game_points.append(task_points)

        response = AllPointsByGame(
            externalGameId=game.externalGameId,
            created_at=str(game.created_at),
            task=game_points,
        )
        return response

    async def get_points_by_gameId_with_details(
        self,
        gameId: UUID,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> AllPointsByGame:
        """
        Aggregate a game's points including per-award detail.

        Like :meth:`get_points_by_gameId` but the result carries the detailed
        per-award breakdown for each task/user.

        Args:
            gameId (UUID): Internal game identifier.
            api_key (str): Caller's API key, used when ``enforce_scope``.
            oauth_user_id (str): Caller's OAuth subject, used when scoping.
            is_admin (bool): Whether the caller has the admin role.
            enforce_scope (bool): When ``True``, verify access to the game.

        Returns:
            AllPointsByGame: The game's aggregated points with detail.

        Raises:
            NotFoundError: If the game does not exist.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_column(
                "id", gameId, not_found_message=f"Game with gameId: {gameId} not found"
            )
        tasks = await self.task_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )

        if not tasks:
            raise NotFoundError(detail=f"Tasks not found by gameId: {game.id}")
        game_points = []
        for task in tasks:
            user_points = []
            points = await self.user_points_repository.get_points_and_users_by_taskId(
                task.id
            )
            if points:

                for point in points:
                    points_of_user = PointsAssignedToUserDetails(
                        externalUserId=point.externalUserId,
                        points=point.points,
                        timesAwarded=point.timesAwarded,
                        pointsData=point.pointsData,
                    )
                    user_points.append(points_of_user)

            task_points = TaskPointsByGame(
                externalTaskId=task.externalTaskId, points=user_points
            )
            game_points.append(task_points)

        response = AllPointsByGame(
            externalGameId=game.externalGameId,
            created_at=str(game.created_at),
            task=game_points,
        )
        return response

    async def get_points_of_user_in_game(
        self,
        gameId,
        externalUserId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> list[PointsAssignedToUser]:
        """
        Return one user's point awards within a single game.

        Args:
            gameId: Internal game identifier.
            externalUserId: External identifier of the user.
            api_key (str): Caller's API key, used when ``enforce_scope``.
            oauth_user_id (str): Caller's OAuth subject, used when scoping.
            is_admin (bool): Whether the caller has the admin role.
            enforce_scope (bool): When ``True``, verify access to the game.

        Returns:
            list[PointsAssignedToUser]: The user's awards in the game.

        Raises:
            NotFoundError: If the game or user does not exist.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_column(
                "id", gameId, not_found_raise_exception=False
            )
        if not game:
            raise NotFoundError(detail=f"Game not found by gameId: {gameId}")
        user = await self.users_repository.read_by_column(
            "externalUserId", externalUserId, not_found_raise_exception=False
        )
        if not user:
            raise NotFoundError(
                detail=f"User not found by externalUserId: {externalUserId}"
            )
        tasks = await self.task_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        if not tasks:
            raise NotFoundError(detail=f"Tasks not found by gameId: {game.id}")
        response = []
        for task in tasks:
            points = await self.user_points_repository.get_points_and_users_by_taskId(
                task.id
            )
            if points:
                for point in points:
                    if point.externalUserId == externalUserId:
                        response.append(
                            PointsAssignedToUser(
                                externalUserId=point.externalUserId,
                                points=point.points,
                                timesAwarded=point.timesAwarded,
                            )
                        )
        return response

    async def get_users_points_by_externalGameId(
        self, externalGameId
    ) -> list[ResponseGetPointsByGame]:
        """
        Return per-user point totals for a game identified by external id.

        Args:
            externalGameId: External identifier of the game.

        Returns:
            list[ResponseGetPointsByGame]: Aggregated points per user/task in
            the game.

        Raises:
            NotFoundError: If the game or its tasks do not exist.
        """
        game = await self.game_repository.read_by_column(
            column="externalGameId",
            value=externalGameId,
            not_found_message=(f"Game with externalGameId {externalGameId} not found"),
        )

        tasks = await self.task_repository.read_by_column(
            "gameId", game.id, only_one=False, not_found_raise_exception=False
        )

        if not tasks:
            raise NotFoundError(
                f"The game with externalGameId {externalGameId} has no tasks"
            )

        response = []
        for task in tasks:
            points = await self.user_points_repository.get_points_and_users_by_taskId(
                task.id
            )
            response_by_task = []
            if points:
                for point in points:
                    response_by_task.append(
                        ResponseGetPointsByTask(
                            externalUserId=point.externalUserId, points=point.points
                        )
                    )

            if response_by_task:
                response.append(
                    ResponseGetPointsByGame(
                        externalTaskId=task.externalTaskId, points=response_by_task
                    )
                )

        return response

    async def get_users_points_by_externalTaskId(
        self, externalTaskId
    ) -> list[ResponseGetPointsByTask]:
        """
        Return per-user point totals for a task identified by external id.

        Args:
            externalTaskId: External identifier of the task.

        Returns:
            list[ResponseGetPointsByTask]: Aggregated points per user on the
            task.

        Raises:
            NotFoundError: If the task does not exist.
        """
        task = await self.task_repository.read_by_column(
            column="externalTaskId",
            value=externalTaskId,
            not_found_message=(f"Task with externalTaskId {externalTaskId} not found"),
        )

        points_by_task = (
            await self.user_points_repository.get_points_and_users_by_taskId(task.id)
        )
        cleaned_points_by_task = []
        if points_by_task:
            for point in points_by_task:
                cleaned_points_by_task.append(
                    ResponseGetPointsByTask(
                        externalUserId=point.externalUserId, points=point.points
                    )
                )
        return cleaned_points_by_task

    async def get_users_points_by_externalTaskId_and_externalUserId(
        self, externalTaskId, externalUserId
    ) -> Any:
        """
        Return a single user's points on a single task (both by external id).

        Args:
            externalTaskId: External identifier of the task.
            externalUserId: External identifier of the user.

        Returns:
            Any: The user's points for that task.

        Raises:
            NotFoundError: If the task or user does not exist.
        """
        task = await self.task_repository.read_by_column(
            column="externalTaskId",
            value=externalTaskId,
            not_found_message=(f"Task with externalTaskId {externalTaskId} not found"),
        )
        user = await self.users_repository.read_by_column(
            column="externalUserId",
            value=externalUserId,
            not_found_message=(f"User with externalUserId {externalUserId} not found"),
        )

        points = await self.user_points_repository.read_by_columns(
            {"taskId": task.id, "userId": user.id}
        )

        return points

    async def get_all_points_by_externalUserId(
        self,
        externalUserId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> UserGamePoints:
        """
        Return one user's points aggregated across all their games.

        Args:
            externalUserId: External identifier of the user.
            api_key (str): Caller's API key, used when ``enforce_scope``.
            oauth_user_id (str): Caller's OAuth subject, used when scoping.
            is_admin (bool): Whether the caller has the admin role.
            enforce_scope (bool): When ``True``, verify access to the user.

        Returns:
            UserGamePoints: The user's points grouped by game.

        Raises:
            NotFoundError: If the user does not exist.
        """
        if enforce_scope:
            user_data = await get_authorized_user(
                self.users_repository,
                externalUserId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            user_data = await self.users_repository.read_by_column(
                column="externalUserId",
                value=externalUserId,
                not_found_message=(
                    f"User with externalUserId {externalUserId} not found"
                ),
                not_found_raise_exception=False,
            )
        if not user_data:
            return UserGamePoints(
                externalUserId=externalUserId,
                points=0,
                timesAwarded=0,
                games=[],
                userExists=False,
            )

        tasks = await self.user_points_repository.get_task_by_externalUserId(
            externalUserId
        )

        response = []
        for task in tasks:
            game = await self.game_repository.read_by_column(
                "id", task.gameId, not_found_raise_exception=True
            )
            response.append(
                await self.get_points_by_gameId_with_details(
                    game.id,
                    api_key=api_key,
                    oauth_user_id=oauth_user_id,
                    is_admin=is_admin,
                    enforce_scope=enforce_scope,
                )
            )

        total_points = 0
        total_times_awarded = 0
        games = []
        for game in response:
            for task in game.task:
                task_points = 0
                task_times_awarded = 0
                task_details = []
                for point in task.points:
                    if point.externalUserId == externalUserId:
                        task_points += point.points
                        task_times_awarded += point.timesAwarded
                        if point.points > 0:
                            task_details.append(
                                TaskDetail(
                                    externalTaskId=task.externalTaskId,
                                    pointsData=point.pointsData,
                                )
                            )
                total_points += task_points
                total_times_awarded += task_times_awarded
                if task_points > 0 and len(task_details) > 0:
                    games.append(
                        GameDetail(
                            externalGameId=game.externalGameId,
                            points=task_points,
                            timesAwarded=task_times_awarded,
                            tasks=task_details,
                        )
                    )
        return UserGamePoints(
            externalUserId=externalUserId,
            points=total_points,
            timesAwarded=total_times_awarded,
            games=games,
        )

    async def get_points_of_user(
        self, externalUserId
    ) -> ResponsePointsByExternalUserId:
        """
        Return a user's total points plus a per-task breakdown.

        Args:
            externalUserId: External identifier of the user.

        Returns:
            ResponsePointsByExternalUserId: The summed total and the per-task
            points list.

        Raises:
            NotFoundError: If the user does not exist.
        """
        user = await self.users_repository.read_by_column(
            column="externalUserId",
            value=externalUserId,
            not_found_message=(f"User with externalUserId {externalUserId} not found"),
        )

        points = await self.user_points_repository.get_task_and_sum_points_by_userId(
            user.id
        )

        total_points = 0
        for point in points:
            total_points += point.points

        response = ResponsePointsByExternalUserId(
            externalUserId=externalUserId,
            points=total_points,
            points_by_task=points,  # noqa
        )
        return response

    async def get_points_of_simulated_task(self, externalTaskId, simulationHash) -> Any:
        """
        Return points rows produced by a specific simulation run of a task.

        Args:
            externalTaskId: External identifier of the task.
            simulationHash: Hash identifying the simulation run.

        Returns:
            Any: The points rows belonging to that simulation.
        """
        return await self.user_points_repository.get_points_of_simulated_task(
            externalTaskId, simulationHash
        )

    async def get_all_point_of_tasks_list(self, list_ids_tasks, withData=False) -> Any:
        """
        Return all points rows for a list of task ids.

        Args:
            list_ids_tasks: Internal task ids to fetch points for.
            withData (bool): When ``True``, include the full JSON ``data``
                column; otherwise return a lighter projection.

        Returns:
            Any: The matching points rows.
        """
        return await self.user_points_repository.get_all_point_of_tasks_list(
            list_ids_tasks, withData
        )
