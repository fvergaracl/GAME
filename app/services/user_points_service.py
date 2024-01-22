from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_repository import UserRepository
from app.repository.user_points_repository import UserPointsRepository
from app.schema.user_schema import (
    BaseUser
)
from app.schema.user_points_schema import (
    BaseUserPointsBaseModel,
    ResponseAssignPointsToUser
)
from app.services.base_service import BaseService
from app.core.exceptions import NotFoundError
from datetime import datetime


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
            points = self.user_points_repository.get_points_and_users_by_taskId(
                task)
            response.append(points)
        return response

    def get_users_points_by_externalTaskId(self, externalTaskId):
        task = self.task_repository.read_by_column(
            column="externalTaskId",
            value=externalTaskId,
            not_found_message=f"Task with externalTaskId {externalTaskId} not found",
        )

        points = self.user_points_repository.get_points_and_users_by_taskId(
            task.id)

        return points

    def get_users_points_by_externalTaskId_and_externalUserId(self, externalTaskId, externalUserId):
        task = self.task_repository.read_by_column(
            column="externalTaskId",
            value=externalTaskId,
            not_found_message=f"Task with externalTaskId {externalTaskId} not found",
        )
        user = self.users_repository.read_by_column(
            column="externalUserId",
            value=externalUserId,
            not_found_message=f"User with externalUserId {externalUserId} not found",
        )

        points = self.user_points_repository.read_by_columns(
            {"taskId": task.id, "userId": user.id})

        return points

    def assign_points_to_user(self, schema):

        task = self.task_repository.read_by_column(
            column="externalTaskId",
            value=schema.externalTaskId,
            not_found_message=f"Task with externalTaskId {schema.externalTaskId} not found",
        )
        user = self.users_repository.read_by_column(
            column="externalUserId",
            value=schema.externalUserId,
            not_found_raise_exception=False,
            not_found_message=f"User with externalUserId {schema.externalUserId} not found",
        )
        is_new_user = False
        if not user:
            user_data = BaseUser(externalUserId=schema.externalUserId)
            user = self.users_repository.create(
                user_data
            )
            is_new_user = True
        if (schema.points == None):
            schema.points = 1
            if (schema.description == None):
                schema.description = "Points assigned by strategy"
            else:
                schema.description = schema.description + "| Points assigned by strategy"

        data_user_points = BaseUserPointsBaseModel(
            points=schema.points,
            description=schema.description,
            timestamp=str(datetime.now()),
            userId=user.id,
            taskId=task.id
        )
        user_points = self.user_points_repository.create(
            data_user_points
        )
        response = ResponseAssignPointsToUser(
            points=user_points.points,
            description=user_points.description,
            timestamp=str(user_points.timestamp),
            externalTaskId=schema.externalTaskId,
            externalUserId=schema.externalUserId,
            isNewUser=is_new_user
        )
        return response
