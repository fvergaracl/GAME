"""Points-by-task read queries."""

from typing import Any

from app.core.exceptions import NotFoundError
from app.services.game_access import get_authorized_game
from app.services.task._base import TaskServiceContext


class TaskPointsMixin(TaskServiceContext):
    """Read user-points aggregates scoped to a task."""

    async def get_points_by_task_id(
        self,
        gameId,
        externalTaskId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> Any:
        """
        Retrieves points by task ID.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            list: A list of points associated with the task.
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
                "id",
                gameId,
                not_found_message=f"Game not found with gameId: {gameId}",
                only_one=True,
            )

        task = await self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId
        )
        if not task:
            raise NotFoundError(
                f"Task not found with externalTaskId: {externalTaskId} for "
                f"gameId: {gameId}"
            )

        task_id = task.id

        user_points = await self.user_points_repository.get_all_UserPoints_by_taskId(
            task_id
        )

        return user_points

    async def get_points_of_user_by_task_id(
        self,
        gameId,
        externalTaskId,
        externalUserId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> Any:
        """
        Retrieves points of a user by task ID.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.
            externalUserId (str): The external user ID.

        Returns:
            dict: The user's points details.
        """
        points_task = await self.get_points_by_task_id_with_details(
            gameId,
            externalTaskId,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
            is_admin=is_admin,
            enforce_scope=enforce_scope,
        )
        user_points = list(
            filter(lambda x: x.externalUserId == externalUserId, points_task)
        )

        if not user_points:
            raise NotFoundError(
                f"User not found with externalUserId: {externalUserId} for "
                f"externalTaskId: {externalTaskId} for gameId: {gameId}"
            )
        return user_points[0]

    async def get_points_by_task_id_with_details(
        self,
        gameId,
        externalTaskId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> Any:
        """
        Retrieves points by task ID with details.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            list: A list of points associated with the task.
        """
        if enforce_scope:
            await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )

        task = await self.task_repository.read_by_gameId_and_externalTaskId(
            gameId, externalTaskId
        )
        if not task:
            raise NotFoundError(
                f"Task not found with externalTaskId: {externalTaskId} for "
                f"gameId: {gameId}"
            )

        task_id = task.id

        user_points = await self.user_points_repository.get_all_UserPoints_by_taskId_with_details(  # noqa: E501
            task_id
        )
        return user_points
