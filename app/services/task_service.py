from app.core.exceptions import ConflictError, NotFoundError
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.repository.game_params_repository import GameParamsRepository
from app.repository.task_params_repository import TaskParamsRepository
from app.schema.task_schema import (CreateTask,
                                    CreateTaskPostSuccesfullyCreated, FindTask)
from app.schema.tasks_params_schema import InsertTaskParams
from app.services.base_service import BaseService
from app.services.strategy_service import StrategyService
from app.util.is_valid_slug import is_valid_slug


class TaskService(BaseService):
    def __init__(
        self,
        strategy_service: StrategyService,
        task_repository: TaskRepository,
        game_repository: GameRepository,
        user_repository: UserRepository,
        user_points_repository: UserPointsRepository,
        game_params_repository: GameParamsRepository,
        task_params_repository: TaskParamsRepository,
    ):
        self.strategy_service = strategy_service()
        self.task_repository = task_repository
        self.game_repository = game_repository
        self.user_repository = user_repository
        self.user_points_repository = user_points_repository
        self.game_params_repository = game_params_repository
        self.task_params_repository = task_params_repository
        super().__init__(task_repository)

    def get_tasks_list_by_externalGameId(self, externalGameId, find_query):
        game = self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message=(
                f"Game not found with externalGameId: {externalGameId}"),
        )

        find_task_query = FindTask(
            gameId=game.id, **find_query.dict(exclude_none=True))
        all_tasks = self.task_repository.read_by_gameId(find_task_query)

        strategy_data = self.strategy_service.get_strategy_by_id(
            game.strategyId)

        game_params = self.game_params_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        if game_params:
            for param in game_params:
                if param.key in strategy_data["variables"]:
                    try:
                        param.value = int(param.value)
                    except ValueError:
                        try:
                            param.value = float(param.value)
                        except ValueError:
                            pass
                    type_param = type(param.value)
                    type_strategy_variable = type(
                        strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value
        cleaned_tasks = []
        for task in all_tasks["items"]:

            strategy_data = self.strategy_service.get_strategy_by_id(
                task.strategyId)
            task_params = self.task_params_repository.read_by_column(
                "taskId", task.id, not_found_raise_exception=False,
                only_one=False
            )
            if game_params:
                for param in game_params:
                    if param.key in strategy_data["variables"]:
                        try:
                            param.value = int(param.value)
                        except ValueError:
                            try:
                                param.value = float(param.value)
                            except ValueError:
                                pass
                        type_param = type(param.value)
                        type_strategy_variable = type(
                            strategy_data["variables"][param.key])
                        if type_param == type_strategy_variable:
                            strategy_data["variables"][param.key] = param.value

            if task_params:
                for param in task_params:
                    if param.key in strategy_data["variables"]:
                        try:
                            param.value = int(param.value)
                        except ValueError:
                            try:
                                param.value = float(param.value)
                            except ValueError:
                                pass
                        type_param = type(param.value)
                        type_strategy_variable = type(
                            strategy_data["variables"][param.key])
                        if type_param == type_strategy_variable:
                            strategy_data["variables"][param.key] = param.value
            task_params = task_params if task_params else []
            task_cleaned = task.dict()
            task_cleaned["strategy"] = strategy_data
            task_cleaned["gameParams"] = game_params
            task_cleaned["taskParams"] = task_params
            cleaned_tasks.append(
                task_cleaned
            )
        all_tasks["items"] = cleaned_tasks
        return all_tasks

    def get_task_by_externalGameId_externalTaskId(
            self, externalGameId, externalTaskId):
        game = self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message=(
                f"Game not found with externalGameId: {externalGameId}"),
            only_one=True,
        )

        task = self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId
        )
        if not task:
            raise NotFoundError(
                f"Task not found with externalTaskId: {externalTaskId} for externalGameId: {externalGameId}"  # noqa
            )

        strategy_data = self.strategy_service.get_strategy_by_id(
            task.strategyId)

        game_params = self.game_params_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        if game_params:
            for param in game_params:
                if param.key in strategy_data["variables"]:
                    try:
                        param.value = int(param.value)
                    except ValueError:
                        try:
                            param.value = float(param.value)
                        except ValueError:
                            pass
                    type_param = type(param.value)
                    type_strategy_variable = type(
                        strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value

        task_params = self.task_params_repository.read_by_column(
            "taskId", task.id, not_found_raise_exception=False, only_one=False
        )
        if task_params:
            for param in task_params:
                if param.key in strategy_data["variables"]:
                    try:
                        param.value = int(param.value)
                    except ValueError:
                        try:
                            param.value = float(param.value)
                        except ValueError:
                            pass
                    type_param = type(param.value)
                    type_strategy_variable = type(
                        strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value

        response = CreateTaskPostSuccesfullyCreated(
            externalTaskId=task.externalTaskId,
            externalGameId=externalGameId,
            gameParams=game_params,
            taskParams=task_params,
            strategy=strategy_data,
            message=f"Task found successfully with externalTaskId: {task.externalTaskId} for externalGameId: {externalGameId} "  # noqa
        )

        return response

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

        new_task_dict = create_query.dict()
        new_task_dict["gameId"] = str(game_id)
        if strategy_id:
            new_task_dict["strategyId"] = str(strategy_id)
        new_task = CreateTask(**new_task_dict)

        created_task = self.task_repository.create(new_task)
        created_params = []
        params = create_query.params
        if params:
            del create_query.params

            for param in params:
                params_dict = param.dict()
                params_dict["taskId"] = str(created_task.id)

                params_to_insert = InsertTaskParams(**params_dict)
                created_param = self.task_params_repository.create(
                    params_to_insert)
                created_params.append(created_param)

        game_params = self.game_params_repository.read_by_column(
            "gameId", game_id, not_found_raise_exception=False, only_one=False
        )

        if game_params:
            for param in game_params:
                if param.key in strategy_data["variables"]:
                    try:
                        param.value = int(param.value)
                    except ValueError:
                        try:
                            param.value = float(param.value)
                        except ValueError:
                            pass
                    type_param = type(param.value)
                    type_strategy_variable = type(
                        strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value

        if created_params:
            for param in created_params:
                if param.key in strategy_data["variables"]:
                    try:
                        param.value = int(param.value)
                    except ValueError:
                        try:
                            param.value = float(param.value)
                        except ValueError:
                            pass
                    type_param = type(param.value)
                    type_strategy_variable = type(
                        strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value

        response = CreateTaskPostSuccesfullyCreated(
            externalTaskId=created_task.externalTaskId,
            externalGameId=externalGameId,
            gameParams=game_params,
            taskParams=created_params,
            strategy=strategy_data,
            message=f"Task created successfully with externalTaskId: {created_task.externalTaskId} for externalGameId: {externalGameId} "  # noqa
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
                strategyId, not_found_message="Strategy not found by id : {strategyId}"  # noqa
            )
        return {"task": task, "strategy": strategy}

    def get_points_by_task_id(self, externalGameId, externalTaskId):
        game = self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message=(
                f"Game not found with externalGameId: {externalGameId}"),
            only_one=True,
        )

        task = self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId
        )
        if not task:
            raise NotFoundError(
                f"Task not found with externalTaskId: {externalTaskId} for externalGameId: {externalGameId}"  # noqa
            )

        task_id = task.id

        user_points = self.user_points_repository.get_all_UserPoints_by_taskId(
            task_id)

        return user_points
