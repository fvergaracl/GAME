from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.schema.task_schema import (CreateTask,
                                    CreateTaskPostSuccesfullyCreated, FindTask,
                                    TaskPointsResponse)
from app.services.base_service import BaseService
from app.services.strategy_service import StrategyService
from app.engine.all_engine_strategies import all_engine_strategies
from app.util.is_valid_slug import is_valid_slug


class TaskService(BaseService):
    def __init__(
        self,
        strategy_service: StrategyService,
        task_repository: TaskRepository,
        game_repository: GameRepository,
        user_repository: UserRepository,
        user_points_repository: UserPointsRepository,
    ):
        self.strategy_service = strategy_service()
        self.task_repository = task_repository
        self.game_repository = game_repository
        self.user_repository = user_repository
        self.user_points_repository = user_points_repository
        super().__init__(task_repository)

    def get_tasks_list_by_externalGameId(self, find_query):
        externalGameId = find_query.externalGameId

        game = self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message=(
                f"Game not found with externalGameId: {externalGameId}"),
        )

        del find_query.externalGameId
        find_task_query = FindTask(
            gameId=game.id, **find_query.dict(exclude_none=True))
        return self.task_repository.read_by_gameId(find_task_query)

    def create_task_by_externalGameId(self, externalGameId, create_query):
        game = self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message=(
                f"Game not found with externalGameId: {externalGameId}"),
            only_one=True,
        )

        externalTaskId = create_query.externalTaskId
        is_valid_externalTaskId = is_valid_slug(externalTaskId)
        if not is_valid_externalTaskId:
            raise ConflictError(
                f"Invalid externalTaskId: {externalTaskId}. It should be a valid slug (Should have only alphanumeric characters and Underscore . Length should be between 3 and 60)"  # noqa
            )

        exist_task = self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId
        )
        if exist_task:
            raise ConflictError(
                f"Task already exists with externalTaskId: {externalTaskId} for externalGameId: {externalGameId}"  # noqa
            )

        return self.create_task_by_game_id(
            game.id,
            game.externalGameId,
            create_query)

    def create_task_by_game_id(
            self,
            game_id,
            externalGameId,
            create_query):
        # Check if the game exists

        if not self.game_repository.read_by_id(
            game_id, not_found_raise_exception=False
        ):
            raise NotFoundError(f"Game not found with gameId: {game_id}")

        strategy_id = create_query.strategyId

        # Check if the strategy exists
        strategy_data = None
        if strategy_id:
            strategy_data = self.strategy_service.get_strategy_by_id(
                strategy_id)
            if not strategy_data:
                raise NotFoundError(
                    f"Strategy not found with strategyId: {strategy_id}")

        if not strategy_id:
            strategy_id = "default"
        strategy_data = self.strategy_service.get_strategy_by_id(strategy_id)

        strategy_id = str(strategy_id)
        if strategy_id == "None":
            strategy_id = None
        # strategy_data = self.strategy_repository.read_by_id(
        #     strategy_id, not_found_raise_exception=False
        # )

        new_task_dict = create_query.dict()
        new_task_dict["gameId"] = str(game_id)
        if strategy_id:
            new_task_dict["strategyId"] = str(strategy_id)
        new_task = CreateTask(**new_task_dict)

        created_task = self.task_repository.create(new_task)

        print('**********************************************')
        response = CreateTaskPostSuccesfullyCreated(
            externalTaskId=created_task.externalTaskId,
            externalGameId=externalGameId,
            strategy=strategy_data,
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
        all_points = self.user_points_repository.get_points_and_users_by_taskId(
            taskId)
        response = TaskPointsResponse(
            externalTaskId=task.externalTaskId, points=all_points
        )
        return response
