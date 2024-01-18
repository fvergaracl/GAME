from app.repository.user_points_repository import UserPointsRepository
from app.services.base_service import BaseService


class UserPointsService(BaseService):
    def __init__(self, user_points_repository: UserPointsRepository):
        self.user_points_repository = user_points_repository
        super().__init__(user_points_repository)
