from app.repository.game_repository import GameRepository
from app.repository.game_params_repository import GameParamsRepository
from app.schema.games_schema import (
    PostCreateGame,
    GameCreated,
    PatchGame,
    FindGameById
)
from app.schema.games_params_schema import InsertGameParams
from app.services.base_service import BaseService
from app.core.exceptions import ConflictError
from uuid import UUID


class GameService(BaseService):
    def __init__(
            self,
            game_repository: GameRepository,
            game_params_repository: GameParamsRepository
    ):
        self.game_repository = game_repository
        self.game_params_repository = game_params_repository
        super().__init__(game_repository)

    def get_by_id(self, id: UUID):
        response = self._repository.get_game_by_id(id)
        return response

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
        created_params = []
        game = self.game_repository.create(schema)

        if params:
            del schema.params

            for param in params:
                # BaseGameParams
                params_dict = param.dict()
                params_dict['gameId'] = str(game.id)

                params_to_insert = InsertGameParams(**params_dict)
                created_param = self.game_params_repository.create(
                    params_to_insert)

                created_params.append(created_param)

        response = GameCreated(
            **game.dict(),
            params=created_params,
            message="Successfully created"
        )
        return response

    def patch_game_by_id(self, id: UUID, schema: PatchGame):
        params = schema.params
        del schema.params
        print('***********************************************')
        print(schema)
        self.game_repository.patch_game_by_id(id, schema)

        if params:
            for param in params:
                # patch_by_attr
                if (param['id'] and param['paramKey'] and param['value']):
                    self.game_params_repository.update_attr(
                        param.id, "paramKey", param.paramKey)
                    self.game_params_repository.update_attr(
                        param.id, "value", param.value)

        return self.game_repository.get_game_by_id(id)
