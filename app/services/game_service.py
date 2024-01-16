from app.repository.game_repository import GameRepository
from app.schema.games_schema import UpsertGame, FindGameByExternalId
from app.services.base_service import BaseService


class GameService(BaseService):
    def __init__(self, game_repository: GameRepository):
        self.game_repository = game_repository
        super().__init__(game_repository)

    def get_by_externalId(self, schema: FindGameByExternalId):
        return self.game_repository.read_by_externalId(schema)

    def create(self, schema: UpsertGame):
        return self.game_repository.create(schema)
