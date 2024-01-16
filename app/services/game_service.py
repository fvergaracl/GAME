from app.repository.game_repository import GameRepository
from app.schema.games_schema import UpsertGame, FindGame
from app.services.base_service import BaseService


class GameService(BaseService):
    def __init__(self, post_repository: GameRepository):
        self.post_repository = post_repository
        super().__init__(post_repository)

    def add(self, schema: UpsertGame):
        find_game = FindGame(externalGameID__eq=schema.externalGameID)
        game = self.post_repository.read(find_game)
        if game:
            return game
        else:
            return self.post_repository.create(schema)

    def patch(self, id: int, schema: UpsertGame):
        return self.post_repository.update(id, schema)
