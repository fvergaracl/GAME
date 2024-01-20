from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.game_repository import GameRepository
from app.services.base_service import BaseService
from app.services.variables.sub_variables import get_sub_variables_by_name


from app.core.exceptions import NotFoundError


class AveragePointsGameService(BaseService):

    def __init__(
            self,
            task_repository: TaskRepository,
            user_points_repository: UserPointsRepository,
            game_repository: GameRepository

    ):

        self.variable_name = "@AVG_POINTS_GAME"
        self.variable_description = "Average points of game by externalGameId"
        self.sub_variables = [
            get_sub_variables_by_name("#EXTERNAL_GAME_ID")
        ]
        self.task_repository = task_repository
        self.user_points_repository = user_points_repository
        self.game_repository = game_repository
        super().__init__(
            task_repository,
            user_points_repository,
            game_repository,
            self.variable_name,
            self.variable_description,
            self.sub_variables
        )

    def average_points_task(self, externalGameId):
        game = self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message="Game not found with externalGameId : {externalGameId} "
        )
        tasks = self.task_repository.read_by_gameId(game.id)
        if len(tasks) == 0:
            raise NotFoundError(
                detail=f"Tasks not found with gameId : {game.id}")
        sum_points = 0
        for task in tasks:
            user_points = self.user_points_repository.read_by_taskId(task.id)
            for user_point in user_points:
                sum_points += user_point.points
        average_points = sum_points / len(tasks)
        return average_points
