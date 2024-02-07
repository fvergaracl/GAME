from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.repository.game_repository import GameRepository
from app.repository.strategy_repository import StrategyRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.schema.task_schema import (CreateTask,
                                    CreateTaskPostSuccesfullyCreated, FindTask,
                                    TaskPointsResponse)
from app.services.base_service import BaseService


class TaskService(BaseService):
    def __init__(
        self,
        task_repository: TaskRepository,
        game_repository: GameRepository,
        strategy_repository: StrategyRepository,
        user_repository: UserRepository,
        user_points_repository: UserPointsRepository,
    ):
        self.task_repository = task_repository
        self.game_repository = game_repository
        self.strategy_repository = strategy_repository
        self.user_repository = user_repository
        self.user_points_repository = user_points_repository
        super().__init__(task_repository)

    def get_tasks_list_by_externalGameId(self, find_query):
        externalGameId = find_query.externalGameId

        game = self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message=(f"Game not found with externalGameId: {externalGameId}"),
        )

        del find_query.externalGameId
        find_task_query = FindTask(gameId=game.id, **find_query.dict(exclude_none=True))
        return self.task_repository.read_by_gameId(find_task_query)

    def create_task_by_game_id(self, game_id, create_query):
        # Check if the game exists

        if not self.game_repository.read_by_id(
            game_id, not_found_raise_exception=False
        ):
            raise NotFoundError(f"Game not found with gameId: {game_id}")
        strategy_id = create_query.strategyId
        strategy_id = str(strategy_id)
        if strategy_id == "None":
            strategy_id = None
        strategy_data = self.strategy_repository.read_by_id(
            strategy_id, not_found_raise_exception=False
        )

        if strategy_id and not strategy_data:
            raise NotFoundError(f"Strategy not found with strategyId: {strategy_id}")

        new_task_dict = create_query.dict()
        new_task_dict["gameId"] = str(game_id)
        if strategy_id:
            new_task_dict["strategyId"] = str(strategy_id)
        new_task = CreateTask(**new_task_dict)

        if self.task_repository.read_by_gameId_and_externalTaskId(
            game_id, new_task.externalTaskId
        ):
            raise ConflictError(
                "Task already exists with externalTaskId:" f" {new_task.externalTaskId}"
            )
        created_task = self.task_repository.create(new_task)
        task_created, strategy_task_created = (
            self.task_repository.get_task_and_strategy_by_id(created_task.id)
        )

        task_created_dict = task_created.dict()
        task_created_dict["gameId"] = str(task_created_dict["gameId"])
        response = CreateTaskPostSuccesfullyCreated(
            **task_created_dict, strategy=strategy_task_created
        )

        return response

    def get_task_detail_by_id(self, schema):
        taskId = schema.taskId
        task = self.task_repository.read_by_id(
            taskId, not_found_message="Task not found by id : {taskId}"
        )
        strategyId = task.strategyId
        strategy = None
        if strategyId:
            strategy = self.strategy_repository.read_by_id(
                strategyId, not_found_message="Strategy not found by id : {strategyId}"
            )
        return {"task": task, "strategy": strategy}

    def get_points_by_task_id(self, schema):
        taskId = schema.taskId
        task = self.task_repository.read_by_id(
            taskId, not_found_message="Task not found by id : {taskId}"
        )
        all_points = self.user_points_repository.get_points_and_users_by_taskId(taskId)
        response = TaskPointsResponse(
            externalTaskId=task.externalTaskId, points=all_points
        )
        return response
