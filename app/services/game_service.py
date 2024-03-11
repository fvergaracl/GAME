from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.repository.game_params_repository import GameParamsRepository
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.schema.games_params_schema import InsertGameParams
from app.schema.games_schema import (GameCreated, PatchGame, PostCreateGame,
                                     ResponsePatchGame)
from app.services.base_service import BaseService
from app.engine.all_engine_strategies import all_engine_strategies

class GameService(BaseService):
    def __init__(
        self,
        game_repository: GameRepository,
        game_params_repository: GameParamsRepository,
        task_repository: TaskRepository,
    ):
        self.game_repository = game_repository
        self.game_params_repository = game_params_repository
        self.task_repository = task_repository
        super().__init__(game_repository)

    def get_by_id(self, id: UUID):
        response = self._repository.get_game_by_id(id)
        return response

    def get_all_games(self, schema):
        return self.game_repository.get_all_games(schema)

    def get_by_externalId(self, externalGameId: str):
        return self.game_repository.read_by_column(
            "externalGameId", externalGameId)

    def create(self, schema: PostCreateGame):
        params = schema.params
        externalGameId = schema.externalGameId

        externalGameId_exist = self.game_repository.read_by_column(
            "externalGameId", externalGameId, not_found_raise_exception=False
        )
        if externalGameId_exist:
            raise ConflictError(
                detail=(
                    f"Game already exist with externalGameId: "
                    f"{externalGameId}")
            )
        created_params = []
        default_strategyId = schema.strategyId
        
        if (default_strategyId is None):
            default_strategyId = "default"

        strategies = all_engine_strategies()
        strategy = next(
            (strategy for strategy in strategies if strategy.id == default_strategyId),
            None
        )
        if not strategy:
            raise NotFoundError(
                detail=f"Strategy with id: {default_strategyId} not found"
            )
        
        game = self.game_repository.create(schema)
        if params:
            del schema.params

            for param in params:
                # BaseGameParams
                params_dict = param.dict()
                params_dict["gameId"] = str(game.id)

                params_to_insert = InsertGameParams(**params_dict)
                created_param = self.game_params_repository.create(
                    params_to_insert)

                created_params.append(created_param)
                
        print(' - ')
        print(' - ')
        print(' - ')
        print(' - ')
        print(' - ')
        print(game)
        print(created_params)
        print(f"Game with externalGameId: {externalGameId} created")
        print(' * ')
        print(' * ')
        print(' * ')
        print(' * ')
        json = game.dict()
        print(json)
        
        response = GameCreated(
            **game.dict(), params=created_params,
            message=f"Game with externalGameId: {externalGameId} created"
            f" successfully"
        )
        return response

    def patch_game_by_id(self, id: UUID, schema: PatchGame):
        params = schema.params
        del schema.params

        updated_game = self.game_repository.patch_game_by_id(id, schema)
        updated_params = []
        if params:
            for param in params:
                self.game_params_repository.patch_game_params_by_id(
                    param.id, param)
                updated_params.append(param)

        updated_game_dict = updated_game.dict()
        updated_game_dict.pop("params", None)

        response = ResponsePatchGame(
            **updated_game_dict, params=updated_params,
            message="Successfully updated"
        )
        return response

    def get_tasks_by_gameId(self, gameId: UUID):
        game = self.game_repository.read_by_id(gameId)
        if not game:
            raise NotFoundError(detail=f"Game not found by id : {gameId}")

        tasks = self.task_repository.read_by_column(
            "gameId", gameId, not_found_raise_exception=False, only_one=False
        )
        tasks_list = []
        if tasks:
            for task in tasks:
                tasks_list.append(task.dict())
        game_dict = game.dict()
        game_dict["tasks"] = tasks_list

        return game_dict
