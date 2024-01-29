from app.repository.task_repository import TaskRepository
from app.repository.game_repository import GameRepository
from app.repository.strategy_repository import StrategyRepository
from app.services.base_service import BaseService
from app.schema.task_schema import FindTask, CreateTask

from app.core.exceptions import ConflictError, NotFoundError


class TaskService(BaseService):
    def __init__(
            self,
            task_repository: TaskRepository,
            game_repository: GameRepository,
            strategy_repository: StrategyRepository
    ):
        self.task_repository = task_repository
        self.game_repository = game_repository
        self.strategy_repository = strategy_repository
        super().__init__(task_repository)

    def get_tasks_list_by_externalGameId(self, find_query):
        externalGameId = find_query.externalGameId

        game = self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message="Task not found with externalGameId : {externalGameId} "
        )

        del find_query.externalGameId
        find_task_query = FindTask(
            gameId=game.id, **find_query.dict(exclude_none=True))
        return self.task_repository.read_by_gameId(find_task_query)

    def create_task_by_game_id(self, game_id, create_query):
        # Check if the game exists
        if not self.game_repository.read_by_id(game_id):
            raise NotFoundError(f"Game not found with gameId: {game_id}")

        strategy_id = create_query.strategyId
        strategy_data = None

        # Check if the strategy exists, if a strategyId is provided
        if strategy_id:
            if not self.strategy_repository.read_by_id(strategy_id):
                raise NotFoundError(
                    f"Strategy not found with strategyId: {strategy_id}")
            strategy_data = self.strategy_repository.read_by_id(strategy_id)

        # Create the new task
        new_task_dict = create_query.dict()
        new_task_dict['gameId'] = str(game_id)
        new_task = CreateTask(**new_task_dict)

        # Check if the task with the same externalTaskId already exists
        if self.task_repository.read_by_gameId_and_externalTaskId(game_id, new_task.externalTaskId):
            raise ConflictError(
                f"Task already exists with externalTaskId: {new_task.externalTaskId}")

        # Create and retrieve the newly created task
        created_task = self.task_repository.create(new_task)
        task_with_strategy = self.task_repository.get_task_and_strategy_by_id(
            created_task.id)
        # ACAAAAA
        print(' ')
        print(' ')
        print(' ')
        print(' ')
        print(' ')
        print('---------------------------------------')
        print(task_with_strategy)
        print('---------------------------------------')
        print(' ')
        print(strategy_data)
        print('*****************************************')
        response = {
            "externalTaskId": task_with_strategy.externalTaskId,
            "externalGameId": task_with_strategy.externalGameId,
            "strategy": strategy_data
        }
        print(response)
        return response

    def get_task_by_externalGameId_and_externalTaskId(self, schema):
        externalGameId = schema.externalGameId
        externalTaskId = schema.externalTaskId

        game = self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message="Game not found with externalGameId : {externalGameId} "
        )

        task = self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId)
        if (task):
            response_dict = {
                "externalTaskId": task.externalTaskId,
                "gameId": task.gameId,
                "externalGameId": externalGameId
            }
            return response_dict

        raise NotFoundError(
            detail=f"Task not found with externalTaskId : \"{externalTaskId}\" To game with externalGameId : \"{externalGameId}\"")
