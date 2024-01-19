from app.repository.task_repository import TaskRepository
from app.repository.game_repository import GameRepository
from app.services.base_service import BaseService
from app.schema.task_schema import FindTask, BaseTask

from app.core.exceptions import ConflictError, NotFoundError


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
            externalGameId, not_found_message="Task not found with externalGameId : {externalGameId} ")
        del find_query.externalGameId
        find_task_query = FindTask(
            gameId=game.id, **find_query.dict(exclude_none=True))
        return self.task_repository.read_by_gameId(find_task_query)

    def create_task_by_externalGameId(self, create_query):
        externalGameId = create_query.externalGameId
        game = self.game_repository.read_by_externalId(
            externalGameId, not_found_message="Game not found with externalGameId : {externalGameId} ")

        del create_query.externalGameId
        create_query_dict = create_query.dict(exclude_none=True)
        create_query_dict['gameId'] = game.id
        externalTaskId = create_query_dict.get('externalTaskId')
        create_query = BaseTask(**create_query_dict)
        is_exist = self.task_repository.read_by_gameId_and_externalTaskId(
            create_query.gameId, create_query.externalTaskId)
        if (is_exist):
            detail = f"Task already exist with externalTaskId : \"{externalTaskId}\" To game with externalGameId : \"{externalGameId}\""
            raise ConflictError(
                detail=detail)

        created_task = self.task_repository.create(create_query)
        if (created_task):
            response_dict = {
                "externalTaskId": created_task.externalTaskId,
                "gameId": created_task.gameId,
                "externalGameId": externalGameId
            }
            return response_dict

    def get_task_by_externalGameId_and_externalTaskId(self, schema):
        externalGameId = schema.externalGameId
        externalTaskId = schema.externalTaskId
        game = self.game_repository.read_by_externalId(
            externalGameId, not_found_message="Game not found with externalGameId : {externalGameId} ")
        if (not game):
            raise NotFoundError(
                detail=f"Game not found with externalGameId : \"{externalGameId}\"")

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
