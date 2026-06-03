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
        semaphore = asyncio.Semaphore(FANOUT_LIMIT)

        async def _fetch(user) -> UserGamePoints:
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
        return await self.user_points_repository.get_points_of_simulated_task(
            externalTaskId, simulationHash
        )

    async def get_all_point_of_tasks_list(self, list_ids_tasks, withData=False) -> Any:
        return await self.user_points_repository.get_all_point_of_tasks_list(
            list_ids_tasks, withData
        )
