from app.core.exceptions import NotFoundError
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.repository.wallet_repository import WalletRepository
from app.schema.user_points_schema import (ResponseGetPointsByGame,
                                           ResponseGetPointsByTask,
                                           ResponsePointsByExternalUserId)
from app.services.base_service import BaseService


class UserPointsService(BaseService):
    def __init__(
        self,
        user_points_repository: UserPointsRepository,
        users_repository: UserRepository,
        game_repository: GameRepository,
        task_repository: TaskRepository,
        wallet_repository: WalletRepository,
    ):
        self.user_points_repository = user_points_repository
        self.users_repository = users_repository
        self.game_repository = game_repository
        self.task_repository = task_repository
        self.wallet_repository = wallet_repository
        super().__init__(user_points_repository)

    def get_users_points_by_externalGameId(self, externalGameId):
        game = self.game_repository.read_by_column(
            column="externalGameId",
            value=externalGameId,
            not_found_message=(f"Game with externalGameId {externalGameId} not found"),
        )

        tasks = self.task_repository.read_by_column(
            "gameId", game.id, only_one=False, not_found_raise_exception=False
        )

        if tasks:
            tasks = [task.id for task in tasks]

        if not tasks:
            raise NotFoundError(
                f"The game with externalGameId {externalGameId} has no tasks"
            )

        response = []
        for task in tasks:
            points = self.user_points_repository.get_points_and_users_by_taskId(task)
            response_by_task = []
            if points:
                for point in points:
                    response_by_task.append(
                        ResponseGetPointsByTask(
                            externalUserId=point.externalUserId, points=point.points
                        )
                    )

            if response_by_task:
                response.append(
                    ResponseGetPointsByGame(
                        externalTaskId=point.externalTaskId, points=response_by_task
                    )
                )

        return response

    def get_users_points_by_externalTaskId(self, externalTaskId):
        task = self.task_repository.read_by_column(
            column="externalTaskId",
            value=externalTaskId,
            not_found_message=(f"Task with externalTaskId {externalTaskId} not found"),
        )

        points_by_task = self.user_points_repository.get_points_and_users_by_taskId(
            task.id
        )
        cleaned_points_by_task = []
        if points_by_task:
            for point in points_by_task:
                cleaned_points_by_task.append(
                    ResponseGetPointsByTask(
                        externalUserId=point.externalUserId, points=point.points
                    )
                )
        return cleaned_points_by_task

    def get_users_points_by_externalTaskId_and_externalUserId(
        self, externalTaskId, externalUserId
    ):
        task = self.task_repository.read_by_column(
            column="externalTaskId",
            value=externalTaskId,
            not_found_message=(f"Task with externalTaskId {externalTaskId} not found"),
        )
        user = self.users_repository.read_by_column(
            column="externalUserId",
            value=externalUserId,
            not_found_message=(f"User with externalUserId {externalUserId} not found"),
        )

        points = self.user_points_repository.read_by_columns(
            {"taskId": task.id, "userId": user.id}
        )

        return points

    def get_points_of_user(self, externalUserId):
        user = self.users_repository.read_by_column(
            column="externalUserId",
            value=externalUserId,
            not_found_message=(f"User with externalUserId {externalUserId} not found"),
        )

        points = self.user_points_repository.get_task_and_sum_points_by_userId(user.id)

        total_points = 0
        for point in points:
            total_points += point.points

        response = ResponsePointsByExternalUserId(
            externalUserId=externalUserId, points=total_points, points_by_task=points
        )
        return response
