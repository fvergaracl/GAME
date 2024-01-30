from app.repository.user_repository import UserRepository
from app.repository.user_points_repository import UserPointsRepository
from app.services.base_service import BaseService
from app.schema.user_points_schema import PostAssignPointsToUser


class UserService(BaseService):
    def __init__(
            self,
            user_repository: UserRepository,
            user_points_repository: UserPointsRepository
    ):
        self.user_repository = user_repository
        self.user_points_repository = user_points_repository
        super().__init__(user_repository)

    def create_user(self, schema):
        return self.user_repository.create(schema)

    def assign_points_to_user(
            self,
            userId,
            schema: PostAssignPointsToUser
    ):
        user = self.user_repository.read_by_id(
            userId,
            not_found_message=f"User not found with userId: {userId}"
        )
        points = schema.points
        if not points:
            # ACA se debe llamar a la funcion que calcula los puntos WIP
            raise ValueError("Points must be provided")
        user_points = self.user_points_repository.create(
            schema, userId=user.id)
        return user_points
