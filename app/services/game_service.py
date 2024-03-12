from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.repository.game_params_repository import GameParamsRepository
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.schema.games_params_schema import InsertGameParams
from app.schema.games_schema import (GameCreated, PatchGame, PostCreateGame,
                                     ResponsePatchGame, BaseGameResult)
from app.services.base_service import BaseService
from app.engine.all_engine_strategies import all_engine_strategies
from app.util.is_valid_slug import is_valid_slug
from app.util.are_variables_matching import are_variables_matching


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

    def get_by_id(self, externalId: str):
        response = self.game_repository.read_by_column(
            "externalGameId", externalId, not_found_raise_exception=True, only_one=True, not_found_message=f"Game not found by externalId: {externalId} "  # noqa
        )

        params = self.game_params_repository.read_by_column(
            "gameId", response.id, not_found_raise_exception=False, only_one=False  # noqa
        )
        response_dict = response.dict()
        response_dict["params"] = params

        response = BaseGameResult(**response_dict)

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

        is_valid_externalGameId = is_valid_slug(externalGameId)
        if not is_valid_externalGameId:
            raise ConflictError(
                detail=(
                    f"Invalid externalGameId: {externalGameId}. externalGameId should be a valid slug (Should have only alphanumeric characters and Underscore . Length should be between 3 and 60)"  # noqa
                )
            )

        # externalGameId
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
            (strategy for strategy in strategies if strategy.id == default_strategyId),  # noqa
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

        response = GameCreated(
            **game.dict(), params=created_params,
            message=f"Game with externalGameId: {externalGameId} created"
            f" successfully"
        )
        return response

    def pacth_game_by_externalGameId(
            self, externalGameId: str, schema: PatchGame
    ):
        game = self.game_repository.read_by_column(
            "externalGameId", externalGameId, not_found_raise_exception=True
        )
        is_matching = are_variables_matching(schema.dict(), game.dict())
        if is_matching:
            raise ConflictError(
                detail="It is not possible to update the game with the same data"  # noqa
            )

        if schema.dict() == game.dict():
            raise ConflictError(
                detail="No difference between schema and game"
            )

        strategyId = schema.strategyId
        if strategyId:
            strategies = all_engine_strategies()
            strategy = next(
                (strategy for strategy in strategies if (
                    strategy.id == strategyId
                )),
                None
            )
            if not strategy:
                raise NotFoundError(
                    detail=f"Strategy with id: {strategyId} not found"
                )
        if not strategyId:
            strategyId = game.strategyId
        if not strategyId:
            strategyId = "default"
        return self.patch_game_by_id(game.id, schema)

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
            message=f"Game with externalGameId: {updated_game.externalGameId} updated successfully"  # noqa
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
