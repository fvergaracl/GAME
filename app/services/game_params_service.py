from app.repository.game_repository import GameRepository
from app.schema.games_schema import UpsertGame, FindGameByExternalId
from app.services.base_service import BaseService


class GameParamsService(BaseService):
    def __init__(self, game_repository: GameRepository):
        self.game_repository = game_repository
        super().__init__(game_repository)
