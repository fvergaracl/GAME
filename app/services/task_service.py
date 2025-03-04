from app.core.exceptions import ConflictError, NotFoundError
from app.repository.game_params_repository import GameParamsRepository
from app.repository.game_repository import GameRepository
from app.repository.task_params_repository import TaskParamsRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.schema.task_schema import (CreateTask, CreateTaskPostSuccesfullyCreated,
                                    FindTask)
from app.schema.tasks_params_schema import InsertTaskParams
from app.services.base_service import BaseService
from app.services.strategy_service import StrategyService


class TaskService(BaseService):
    """
    Service class for managing tasks.

    Attributes:
        strategy_service (StrategyService): Service instance for strategies.
        task_repository (TaskRepository): Repository instance for tasks.
        game_repository (GameRepository): Repository instance for games.
        user_repository (UserRepository): Repository instance for users.
        user_points_repository (UserPointsRepository): Repository instance for
          user points.
        game_params_repository (GameParamsRepository): Repository instance for
          game parameters.
        task_params_repository (TaskParamsRepository): Repository instance for
          task parameters.
    """

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
        """
        Initializes the TaskService with the provided repositories and
          services.

        Args:
            strategy_service (StrategyService): The strategy service instance.
            task_repository (TaskRepository): The task repository instance.
            game_repository (GameRepository): The game repository instance.
            user_repository (UserRepository): The user repository instance.
            user_points_repository (UserPointsRepository): The user points
              repository instance.
            game_params_repository (GameParamsRepository): The game parameters
              repository instance.
            task_params_repository (TaskParamsRepository): The task parameters
              repository instance.
        """
        self.strategy_service = strategy_service()
        self.task_repository = task_repository
        self.game_repository = game_repository
        self.user_repository = user_repository
        self.user_points_repository = user_points_repository
        self.game_params_repository = game_params_repository
        self.task_params_repository = task_params_repository
        super().__init__(task_repository)

    def get_tasks_list_by_externalGameId(self, externalGameId, find_query):
        """
        Retrieves a list of tasks associated with a game by its external game
          ID.

        Args:
            externalGameId (str): The external game ID.
            find_query: The query for finding tasks.

        Returns:
            list: A list of tasks associated with the game.
        """
        game = self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message=f"Game not found with externalGameId: "
            f"{externalGameId}",
        )

        if not game:
            raise NotFoundError(f"Game not found with externalGameId: {externalGameId}")

        return self.get_tasks_list_by_gameId(game.id, find_query)

    def get_tasks_list_by_gameId(self, gameId, find_query):
        """
        Retrieves a list of tasks associated with a game by its game ID.

        Args:
            gameId (UUID): The game ID.
            find_query: The query for finding tasks.

        Returns:
            list: A list of tasks associated with the game.
        """
        game = self.game_repository.read_by_id(gameId, not_found_raise_exception=False)

        if not game:
            raise NotFoundError(f"Game not found with gameId: {gameId}")

        find_task_query = FindTask(gameId=game.id, **find_query.dict(exclude_none=True))
        all_tasks = self.task_repository.read_by_gameId(find_task_query)

        strategy_data = self.strategy_service.get_strategy_by_id(game.strategyId)
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
                    type_strategy_variable = type(strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value
        cleaned_tasks = []
        for task in all_tasks["items"]:
            strategy_data = self.strategy_service.get_strategy_by_id(task.strategyId)
            task_params = self.task_params_repository.read_by_column(
                "taskId", task.id, not_found_raise_exception=False, only_one=False
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
                            strategy_data["variables"][param.key]
                        )
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
                            strategy_data["variables"][param.key]
                        )
                        if type_param == type_strategy_variable:
                            strategy_data["variables"][param.key] = param.value
            task_params = task_params if task_params else []
            task_cleaned = task.dict()
            task_cleaned["strategy"] = strategy_data
            task_cleaned["gameParams"] = game_params
            task_cleaned["taskParams"] = task_params
            cleaned_tasks.append(task_cleaned)
        all_tasks["items"] = cleaned_tasks
        return all_tasks

    def get_task_by_gameId_externalTaskId(self, gameId, externalTaskId):
        """
        Retrieves a task by its game ID and external task ID.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            CreateTaskPostSuccesfullyCreated: The task details.
        """
        game = self.game_repository.read_by_id(gameId, not_found_raise_exception=False)
        if not game:
            raise NotFoundError(f"Game not found with gameId: {gameId}")

        task = self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId
        )
        if not task:
            raise NotFoundError(
                f"Task not found with externalTaskId: {externalTaskId} for "
                f"gameId: {gameId}"
            )

        strategy_data = self.strategy_service.get_strategy_by_id(task.strategyId)

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
                    type_strategy_variable = type(strategy_data["variables"][param.key])
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
                    type_strategy_variable = type(strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value

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

    def get_task_by_externalGameId_externalTaskId(self, gameId, externalTaskId):
        """
        Retrieves a task by its game ID and external task ID.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            CreateTaskPostSuccesfullyCreated: The task details.
        """
        game = self.game_repository.read_by_column(
            "id",
            gameId,
            not_found_message=f"Game not found with id: " f"{gameId}",
            only_one=True,
        )

        return self.get_task_by_gameId_externalTaskId(game.id, externalTaskId)

    def create_task_by_externalGameId(self, externalGameId, create_query):
        """
        Creates a task for a game by its external game ID.

        Args:
            externalGameId (str): The external game ID.
            create_query: The query for creating the task.

        Returns:
            CreateTaskPostSuccesfullyCreated: The created task details.
        """
        game = self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message=f"Game not found with externalGameId: "
            f"{externalGameId}",
            only_one=True,
        )

        return self.create_task_by_game_id(game.id, externalGameId, create_query)

    async def create_task_by_game_id(self, gameId, create_query, api_key: str = None):
        """
        Creates a task for a game by its game ID.

        Args:
            gameId (UUID): The game ID.
            create_query: The query for creating the task.

        Returns:
            CreateTaskPostSuccesfullyCreated: The created task details.
        """
        game_data = self.game_repository.read_by_id(
            gameId, not_found_raise_exception=False
        )
        if not game_data:
            raise NotFoundError(f"Game not found with gameId: {gameId}")

        task = self.task_repository.read_by_gameId_and_externalTaskId(
            gameId, create_query.externalTaskId
        )
        if task:
            raise ConflictError(
                f"Task already exists with externalTaskId: "
                f"{create_query.externalTaskId} for gameId: {gameId}"
            )

        strategy_id = create_query.strategyId

        strategy_data = None
        if strategy_id:
            strategy_data = self.strategy_service.get_strategy_by_id(strategy_id)
            if not strategy_data:
                raise NotFoundError(
                    f"Strategy not found with strategyId: {strategy_id}"
                )

        if not strategy_id:
            strategy_id = "default"
        strategy_data = self.strategy_service.get_strategy_by_id(strategy_id)

        strategy_id = str(strategy_id)

        new_task_dict = create_query.dict()
        new_task_dict["gameId"] = str(gameId)
        if strategy_id:
            new_task_dict["strategyId"] = str(strategy_id)
        if api_key:
            new_task_dict["apiKey_used"] = api_key
        new_task = CreateTask(**new_task_dict)

        created_task = await self.task_repository.create(new_task)
        created_params = []
        params = create_query.params
        if params:
            del create_query.params

            for param in params:
                params_dict = param.dict()
                params_dict["taskId"] = str(created_task.id)
                params_dict["value"] = str(params_dict["value"])
                if api_key:
                    params_dict["apiKey_used"] = api_key
                params_to_insert = InsertTaskParams(**params_dict)
                created_param = await self.task_params_repository.create(
                    params_to_insert
                )
                created_params.append(created_param)

        game_params = self.game_params_repository.read_by_column(
            "gameId", gameId, not_found_raise_exception=False, only_one=False
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
                    type_strategy_variable = type(strategy_data["variables"][param.key])
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
                    type_strategy_variable = type(strategy_data["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy_data["variables"][param.key] = param.value
        externalGameId = game_data.externalGameId
        response = CreateTaskPostSuccesfullyCreated(
            externalTaskId=created_task.externalTaskId,
            externalGameId=externalGameId,
            gameParams=game_params,
            taskParams=created_params,
            strategy=strategy_data,
            message=f"Task created successfully with externalTaskId: "
            f"{created_task.externalTaskId} for gameId: {gameId}",
        )

        return response

    def get_task_detail_by_id(self, schema):
        """
        Retrieves task details by its ID.

        Args:
            schema: The schema containing the task ID.

        Returns:
            dict: The task and strategy details.
        """
        taskId = schema.taskId
        task = self.task_repository.read_by_id(
            taskId, not_found_message="Task not found by id: {taskId}"
        )
        strategyId = task.strategyId
        strategy = None
        if strategyId:
            strategy = self.strategy_repository.read_by_id(
                strategyId,
                not_found_message="Strategy not found by id: " f"{strategyId}",
            )
        return {"task": task, "strategy": strategy}

    def get_points_by_task_id(self, gameId, externalTaskId):
        """
        Retrieves points by task ID.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            list: A list of points associated with the task.
        """
        game = self.game_repository.read_by_column(
            "id",
            gameId,
            not_found_message=f"Game not found with gameId: {gameId}",
            only_one=True,
        )

        task = self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId
        )
        if not task:
            raise NotFoundError(
                f"Task not found with externalTaskId: {externalTaskId} for "
                f"gameId: {gameId}"
            )

        task_id = task.id

        user_points = self.user_points_repository.get_all_UserPoints_by_taskId(task_id)

        return user_points

    def get_points_of_user_by_task_id(self, gameId, externalTaskId, externalUserId):
        """
        Retrieves points of a user by task ID.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.
            externalUserId (str): The external user ID.

        Returns:
            dict: The user's points details.
        """
        points_task = self.get_points_by_task_id_with_details(gameId, externalTaskId)
        user_points = list(
            filter(lambda x: x.externalUserId == externalUserId, points_task)
        )

        if not user_points:
            raise NotFoundError(
                f"User not found with externalUserId: {externalUserId} for "
                f"externalTaskId: {externalTaskId} for gameId: {gameId}"
            )
        return user_points[0]

    def get_points_by_task_id_with_details(self, gameId, externalTaskId):
        """
        Retrieves points by task ID with details.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            list: A list of points associated with the task.
        """
        task = self.task_repository.read_by_gameId_and_externalTaskId(
            gameId, externalTaskId
        )
        if not task:
            raise NotFoundError(
                f"Task not found with externalTaskId: {externalTaskId} for "
                f"gameId: {gameId}"
            )

        task_id = task.id

        user_points = self.user_points_repository.get_all_UserPoints_by_taskId_with_details(  # noqa: E501
            task_id
        )
        return user_points

    def get_task_params_by_externalTaskId(self, externalTaskId):
        """
        Retrieves task parameters by external task ID.

        Args:
            externalTaskId (str): The external task ID.

        Returns:
            list: A list of task parameters associated with the task.
        """
        task = self.task_repository.read_by_column(
            "externalTaskId",
            externalTaskId,
            not_found_message=f"Task not found with externalTaskId: "
            f"{externalTaskId}",
            only_one=True,
        )

        task_id = task.id

        task_params = self.task_params_repository.read_by_column(
            "taskId",
            task_id,
            not_found_raise_exception=False,
            only_one=False,
        )

        return task_params
