from app.repository.task_repository import TaskRepository
from app.repository.game_repository import GameRepository
from app.services.base_service import BaseService
from app.schema.task_schema import FindTask


class TaskService(BaseService):
    def __init__(
            self,
            task_repository: TaskRepository,
            game_repository: GameRepository
    ):
        self.task_repository = task_repository
        self.game_repository = game_repository
        super().__init__(task_repository)

    def get_tasks_list_by_externalGameId(self, find_query):
        externalGameId = find_query.externalGameId
        game = self.game_repository.read_by_externalId(
            externalGameId, not_found_message="Task not found with externalGameId : {externalGameID} ")
        del find_query.externalGameId
        find_task_query = FindTask(
            gameId=game.id, **find_query.dict(exclude_none=True))
        return self.task_repository.read_by_gameId(find_task_query)
