from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_repository import UserRepository
from app.repository.user_points_repository import UserPointsRepository
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundError


class UserPointsService(BaseService):
    def __init__(
            self,
            user_points_repository: UserPointsRepository,
            users_repository: UserRepository,
            game_repository: GameRepository,
            task_repository: TaskRepository
    ):
        self.user_points_repository = user_points_repository
        self.users_repository = users_repository
        self.game_repository = game_repository
        self.task_repository = task_repository
        super().__init__(user_points_repository)

    def get_users_points_by_externalGameId(self, externalGameId):
        game = self.game_repository.read_by_column(
            column="externalGameId",
            value=externalGameId,
            not_found_message=f"Game with externalGameId {externalGameId} not found",
        )

        tasks = self.task_repository.read_by_column(
            "gameId", game.id,
            only_one=False,
            not_found_raise_exception=False
        )

        if tasks:
            tasks = [task.id for task in tasks]

        if not tasks:
            raise NotFoundError(
                f"The game with externalGameId {externalGameId} has no tasks")

        response = []
        for task in tasks:
            user_points = self.user_points_repository.read_by_column(
                "taskId", task,
                only_one=False,
                not_found_raise_exception=False
            )
            
        return response
