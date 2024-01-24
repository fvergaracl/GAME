from app.repository.game_repository import GameRepository
from app.repository.game_params_repository import GameParamsRepository
from app.schema.games_schema import PostCreateGame, FindGameByExternalId, UpdateGame
from app.schema.games_params_schema import BaseGameParams
from app.services.base_service import BaseService

from app.core.exceptions import ConflictError


class GameService(BaseService):
    def __init__(
            self,
            game_repository: GameRepository,
            game_params_repository: GameParamsRepository
    ):
        self.game_repository = game_repository
        self.game_params_repository = game_params_repository
        super().__init__(game_repository)

    def get_all_games(self, schema):
        return self.game_repository.get_all_games(schema)

    def get_by_externalId(self, externalGameId: str):
        return self.game_repository.read_by_column(
            "externalGameId", externalGameId
        )

    def create(self, schema: PostCreateGame):
        params = schema.params
        externalGameId = schema.externalGameId

        externalGameId_exist = self.game_repository.read_by_column(
            "externalGameId", externalGameId,
            not_found_raise_exception=False
        )
        if externalGameId_exist:
            raise ConflictError(
                detail=f"Game already exist with externalGameId : {externalGameId}")

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
