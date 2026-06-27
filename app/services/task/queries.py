"""Task read path: list, lookup-by-id and detail queries."""

from typing import Any

from app.core.exceptions import NotFoundError
from app.schema.task_schema import CreateTaskPostSuccesfullyCreated, FindTask
from app.services.game_access import get_authorized_game
from app.services.task._base import (
    TaskServiceContext,
    apply_strategy_variable_overrides,
)


class TaskQueryMixin(TaskServiceContext):
    """Read-only task lookups and listings."""

    async def get_tasks_list_by_externalGameId(
        self, externalGameId, find_query
    ) -> dict[str, Any]:
        """
        Retrieves a list of tasks associated with a game by its external game
          ID.

        Args:
            externalGameId (str): The external game ID.
            find_query: The query for finding tasks.

        Returns:
            list: A list of tasks associated with the game.
        """
        game = await self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message=f"Game not found with externalGameId: "
            f"{externalGameId}",
        )

        if not game:
            raise NotFoundError(f"Game not found with externalGameId: {externalGameId}")

        return await self.get_tasks_list_by_gameId(game.id, find_query)

    async def get_tasks_list_by_gameId(
        self,
        gameId,
        find_query,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> dict[str, Any]:
        """
        Retrieves a list of tasks associated with a game by its game ID.

        Args:
            gameId (UUID): The game ID.
            find_query: The query for finding tasks.

        Returns:
            list: A list of tasks associated with the game.
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
            game = await self.game_repository.read_by_id(
                gameId, not_found_raise_exception=False
            )

        if not game:
            raise NotFoundError(f"Game not found with gameId: {gameId}")

        find_task_query = FindTask(
            gameId=game.id, **find_query.model_dump(exclude_none=True)
        )
        all_tasks = await self.task_repository.read_by_gameId(find_task_query)

        strategy_data = self.strategy_service.get_strategy_by_id(game.strategyId)
        game_params = await self.game_params_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        apply_strategy_variable_overrides(game_params, strategy_data)
        cleaned_tasks = []
        for task in all_tasks["items"]:
            strategy_data = self.strategy_service.get_strategy_by_id(task.strategyId)
            task_params = await self.task_params_repository.read_by_column(
                "taskId", task.id, not_found_raise_exception=False, only_one=False
            )
            apply_strategy_variable_overrides(game_params, strategy_data)

            apply_strategy_variable_overrides(task_params, strategy_data)
            task_params = task_params if task_params else []
            task_cleaned = task.model_dump()
            task_cleaned["strategy"] = strategy_data
            task_cleaned["gameParams"] = game_params
            task_cleaned["taskParams"] = task_params
            cleaned_tasks.append(task_cleaned)
        all_tasks["items"] = cleaned_tasks
        return all_tasks

    async def get_task_by_gameId_externalTaskId(
        self,
        gameId,
        externalTaskId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> CreateTaskPostSuccesfullyCreated:
        """
        Retrieves a task by its game ID and external task ID.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            CreateTaskPostSuccesfullyCreated: The task details.
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
            game = await self.game_repository.read_by_id(
                gameId, not_found_raise_exception=False
            )
        if not game:
            raise NotFoundError(f"Game not found with gameId: {gameId}")

        task = await self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId
        )
        if not task:
            raise NotFoundError(
                f"Task not found with externalTaskId: {externalTaskId} for "
                f"gameId: {gameId}"
            )

        strategy_data = self.strategy_service.get_strategy_by_id(task.strategyId)

        game_params = await self.game_params_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        apply_strategy_variable_overrides(game_params, strategy_data)

        task_params = await self.task_params_repository.read_by_column(
            "taskId", task.id, not_found_raise_exception=False, only_one=False
        )
        apply_strategy_variable_overrides(task_params, strategy_data)

        response = CreateTaskPostSuccesfullyCreated(
            externalTaskId=task.externalTaskId,
            externalGameId=game.externalGameId,
            gameParams=game_params,
            taskParams=task_params,
            strategy=strategy_data,
            message=f"Task found successfully with externalTaskId: "
            f"{task.externalTaskId} for gameId: {gameId}",
        )

        return response

    async def get_task_by_externalGameId_externalTaskId(
        self,
        gameId,
        externalTaskId,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> CreateTaskPostSuccesfullyCreated:
        """
        Retrieves a task by its game ID and external task ID.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            CreateTaskPostSuccesfullyCreated: The task details.
        """
        game = await self.game_repository.read_by_column(
            "id",
            gameId,
            not_found_message=f"Game not found with id: " f"{gameId}",
            only_one=True,
        )

        return await self.get_task_by_gameId_externalTaskId(
            game.id,
            externalTaskId,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
            is_admin=is_admin,
            enforce_scope=enforce_scope,
        )

    async def get_task_detail_by_id(self, schema) -> dict[str, Any]:
        """
        Retrieves task details by its ID.

        Args:
            schema: The schema containing the task ID.

        Returns:
            dict: The task and strategy details.
        """
        taskId = schema.taskId
        task = await self.task_repository.read_by_id(
            taskId, not_found_message="Task not found by id: {taskId}"
        )
        strategyId = task.strategyId
        strategy = None
        if strategyId:
            strategy = await self.strategy_repository.read_by_id(
                strategyId,
                not_found_message="Strategy not found by id: " f"{strategyId}",
            )
        return {"task": task, "strategy": strategy}

    async def get_task_params_by_externalTaskId(self, externalTaskId) -> Any:
        """
        Retrieves task parameters by external task ID.

        Args:
            externalTaskId (str): The external task ID.

        Returns:
            list: A list of task parameters associated with the task.
        """
        task = await self.task_repository.read_by_column(
            "externalTaskId",
            externalTaskId,
            not_found_message=f"Task not found with externalTaskId: "
            f"{externalTaskId}",
            only_one=True,
        )

        task_id = task.id

        task_params = await self.task_params_repository.read_by_column(
            "taskId",
            task_id,
            not_found_raise_exception=False,
            only_one=False,
        )

        return task_params
