from app.repository.game_repository import GameRepository
from app.repository.game_params_repository import GameParamsRepository
from app.schema.games_schema import CreateGame, FindGameByExternalId, UpdateGame
from app.schema.games_params_schema import BaseGameParams
from app.services.base_service import BaseService


class GameService(BaseService):
    def __init__(self, game_repository: GameRepository, game_params_repository: GameParamsRepository):
        self.game_repository = game_repository
        self.game_params_repository = game_params_repository
        super().__init__(game_repository)

    def get_by_externalId(self, schema: FindGameByExternalId):
        return self.game_repository.read_by_externalId(schema)

    def create(self, schema: CreateGame):
        params = schema.params
        if params:
            del schema.params
            game = self.game_repository.create(schema)
            for param in params:
                # BaseGameParams
                params_dict = param.dict()
                params_dict['gameId'] = game.id
                params_to_insert = BaseGameParams(**params_dict)
                self.game_params_repository.create(params_to_insert)
            return game
        return self.game_repository.create(schema)

    def update(self, id: int, schema: UpdateGame):
        params = schema.params
        if params:
            for param in params:
                self.game_params_repository.update_params_gameId(id, param)
        del schema.params
        return self.game_repository.update(id, schema)
