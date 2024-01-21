from app.services.variables.AVG_POINTS_GAME_BY_USER import AveragePointsGameService
from app.services.variables.AVG_POINTS_TASK_BY_USER import AveragePointsTaskService
from app.services.variables.LAST_PERSONAL_POINTS_GAME import LastPersonalPointsGameService
from app.services.variables.LAST_PERSONAL_POINTS_TASK import LastPersonalPointsTaskService

from app.repository.task_repository import TaskRepository
from app.repository.game_params_repository import GameParamsRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.game_repository import GameRepository


class RulesService():
    def __init__(self, db):
        self.db = db
        self.task_repository = TaskRepository(db)
        self.user_points_repository = UserPointsRepository(db)
        self.game_repository = GameRepository(db)
        self.game_params_repository = GameParamsRepository(db)
        self.average_points_task_service = AveragePointsTaskService(
            self.task_repository, self.user_points_repository)
        self.average_points_game_service = AveragePointsGameService(
            self.task_repository, self.user_points_repository, self.game_repository)
        self.last_personal_points_game_service = LastPersonalPointsGameService(
            self.task_repository, self.game_params_repository, self.user_points_repository)
        self.last_personal_points_task_service = LastPersonalPointsTaskService(
            self.task_repository, self.user_points_repository)

        super().__init__()

    def get_all_variables(self):
        return [
            self.average_points_task_service,
            self.average_points_game_service,
            self.last_personal_points_game_service,
            self.last_personal_points_task_service
        ]
    
