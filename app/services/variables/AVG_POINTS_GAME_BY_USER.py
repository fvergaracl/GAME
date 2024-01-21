from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.game_repository import GameRepository
from app.services.variables.variableBase import VariableBase
from app.services.variables.sub_variables import get_sub_variables_by_name


class AveragePointsGameService(VariableBase):

    def __init__(
            self,
            task_repository: TaskRepository,
            user_points_repository: UserPointsRepository,
            game_repository: GameRepository

    ):

        self.variable_name = "@AVG_POINTS_GAME_BY_USER"
        self.variable_description = "Average points of game by externalGameId"
        self.sub_variables = [
            get_sub_variables_by_name("#EXTERNAL_GAME_ID")
        ]
        self.task_repository = task_repository
        self.user_points_repository = user_points_repository
        self.game_repository = game_repository
        super().__init__(
            self.variable_name,
            self.variable_description,
            self.sub_variables
        )

    def average_points_game_by_user(self, externalGameId):
        game = self.game_repository.read_by_column(
            "externalGameId",
            externalGameId,
            not_found_message="Game not found with externalGameId : {externalGameId} "
        )

        tasks = self.task_repository.read_by_column(
            "gameId",
            game.id,
            only_one=False,
            not_found_raise_exception=False
        )

        if len(tasks) == 0:
            return 0

        sum_points = 0
        for task in tasks:
            user_points = self.user_points_repository.read_by_column(
                "taskId",
                task.id,
                only_one=False,
                not_found_raise_exception=False
            )
            if len(user_points) == 0:
                continue
            for user_point in user_points:
                sum_points += user_point.points
        average_points = sum_points / len(tasks)
        return average_points
