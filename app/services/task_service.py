from app.repository.task_repository import TaskRepository
from app.repository.game_repository import GameRepository
from app.services.base_service import BaseService
from app.schema.task_schema import FindTask, BaseTask

from app.core.exceptions import ConflictError


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
        print('*************************************')
        print(create_query)
        externalGameId = create_query.externalGameId
        game = self.game_repository.read_by_externalId(
            externalGameId, not_found_message="Game not found with externalGameId : {externalGameId} ")
        del create_query.externalGameId
        create_query_dict = create_query.dict(exclude_none=True)
        create_query_dict['gameId'] = game.id
        externalTaskId = create_query_dict.get('externalTaskId')
        create_query_dict['externalTaskId'] = f"{externalGameId}_{externalTaskId}"
        create_query = BaseTask(**create_query_dict)
        print('*************************************11111111')
        print(create_query)
        is_exist = self.task_repository.read_by_externalTaskId(
            create_query.externalTaskId)
        print('*aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        print(is_exist)
        if (is_exist):
            raise ConflictError(
                detail=f"Task already exist with externalTaskId : {externalTaskId}")
        created_task = self.task_repository.create(create_query)
        print('*************************************222222222')
        print(created_task)

        if (created_task):
            response_dict = {
                "externalTaskId": created_task.externalTaskId,
                "gameId": created_task.gameId,
                "externalGameId": externalGameId
            }
            return response_dict
