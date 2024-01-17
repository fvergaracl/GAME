from app.repository.game_params_repository import GameParamsRepository
from app.services.base_service import BaseService


class GameParamsService(BaseService):
    def __init__(self, game_params_repository: GameParamsRepository):
        self.game_params_repository = game_params_repository
        super().__init__(game_params_repository)
