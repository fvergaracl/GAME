from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.engine.all_engine_strategies import all_engine_strategies
from app.repository.game_params_repository import GameParamsRepository
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.schema.games_params_schema import InsertGameParams
from app.schema.games_schema import (BaseGameResult, GameCreated, PatchGame,
                                     PostCreateGame, ResponsePatchGame)
from app.services.base_service import BaseService
from app.services.strategy_service import StrategyService
from app.util.are_variables_matching import are_variables_matching
from app.util.is_valid_slug import is_valid_slug


class GameService(BaseService):
    """
    Service class for managing games.

    Attributes:
        game_repository (GameRepository): Repository instance for games.
        game_params_repository (GameParamsRepository): Repository instance for
          game parameters.
        task_repository (TaskRepository): Repository instance for tasks.
        strategy_service (StrategyService): Service instance for strategies.
    """

    def __init__(
        self,
        game_repository: GameRepository,
        game_params_repository: GameParamsRepository,
        task_repository: TaskRepository,
        strategy_service: StrategyService,
    ):
        """
        Initializes the GameService with the provided repositories and
          services.

        Args:
            game_repository (GameRepository): The game repository instance.
            game_params_repository (GameParamsRepository): The game parameters
              repository instance.
            task_repository (TaskRepository): The task repository instance.
            strategy_service (StrategyService): The strategy service instance.
        """
        self.game_repository = game_repository
        self.game_params_repository = game_params_repository
        self.task_repository = task_repository
        self.strategy_service = strategy_service
        super().__init__(game_repository)

    def get_by_gameId(self, gameId: UUID):
        """
        Retrieves a game by its game ID.

        Args:
            gameId (UUID): The game ID.

        Returns:
            BaseGameResult: The game details.
        """
        response = self.game_repository.read_by_column(
            "id",
            gameId,
            not_found_raise_exception=True,
            only_one=True,
            not_found_message=f"Game not found by gameId: {gameId}",
        )
        params = self.game_params_repository.read_by_column(
            "gameId", response.id, not_found_raise_exception=False, only_one=False
        )
        response_dict = response.dict()
        response_dict["params"] = params

        response = BaseGameResult(**response_dict, gameId=gameId)

        return response

    def get_all_games(self, schema):
        """
        Retrieves all games based on the provided schema.

        Args:
            schema: The schema for filtering the games.

        Returns:
            list: A list of all games matching the schema.
        """
        return self.game_repository.get_all_games(schema)

    def get_by_externalId(self, externalGameId: str):
        """
        Retrieves a game by its external game ID.

        Args:
            externalGameId (str): The external game ID.

        Returns:
            object: The game details.
        """
        return self.game_repository.read_by_column("externalGameId", externalGameId)

    def create(self, schema: PostCreateGame):
        """
        Creates a new game using the provided schema.

        Args:
            schema (PostCreateGame): The schema representing the game to be
              created.

        Returns:
            GameCreated: The created game details.
        """
        params = schema.params
        externalGameId = schema.externalGameId

        externalGameId_exist = self.game_repository.read_by_column(
            "externalGameId", externalGameId, not_found_raise_exception=False
        )

        is_valid_externalGameId = is_valid_slug(externalGameId)
        if not is_valid_externalGameId:
            raise ConflictError(
                detail=(
                    f"Invalid externalGameId: {externalGameId}. externalGameId"
                    f" should be a valid slug (Should have only alphanumeric"
                    f" characters and Underscore. Length should be between 3"
                    f" and 60)"
                )
            )

        if externalGameId_exist:
            raise ConflictError(
                detail=f"Game already exists with externalGameId: " f"{externalGameId}"
            )
        created_params = []
        default_strategyId = schema.strategyId

        if default_strategyId is None:
            default_strategyId = "default"

        strategies = all_engine_strategies()
        strategy = next(
            (strategy for strategy in strategies if strategy.id == default_strategyId),
            None,
        )
        if not strategy:
            raise NotFoundError(
                detail=f"Strategy with id: {default_strategyId} not found"
            )

        game = self.game_repository.create(schema)
        if params:
            del schema.params

            for param in params:
                params_dict = param.dict()
                params_dict["gameId"] = str(game.id)
                params_to_insert = InsertGameParams(**params_dict)
                created_param = self.game_params_repository.create(params_to_insert)

                created_params.append(created_param)

        response = GameCreated(
            **game.dict(),
            params=created_params,
            gameId=game.id,
            message=f"Game with gameId: {game.id} created successfully",
        )
        return response

    def patch_game_by_externalGameId(self, externalGameId: str, schema: PatchGame):
        """
        Updates a game by its external game ID using the provided schema.

        Args:
            externalGameId (str): The external game ID.
            schema (PatchGame): The schema representing the updated data.

        Returns:
            ResponsePatchGame: The updated game details.
        """
        game = self.game_repository.read_by_column(
            "externalGameId", externalGameId, not_found_raise_exception=False
        )
        if not game:
            raise NotFoundError(
                detail=f"Game not found by externalGameId: {externalGameId}"
            )
        return self.patch_game_by_id(game.id, schema)

    def patch_game_by_id(self, gameId: UUID, schema: PatchGame):
        """
        Updates a game by its game ID using the provided schema.

        Args:
            gameId (UUID): The game ID.
            schema (PatchGame): The schema representing the updated data.

        Returns:
            ResponsePatchGame: The updated game details.
        """
        game = self.game_repository.read_by_id(gameId, not_found_raise_exception=False)
        if not game:
            raise NotFoundError(detail=f"Game not found by gameId: {gameId}")
        if schema.externalGameId and schema.externalGameId != game.externalGameId:
            externalGameId_exist = self.game_repository.read_by_column(
                "externalGameId", schema.externalGameId, not_found_raise_exception=False
            )
            if externalGameId_exist:
                raise ConflictError(
                    detail=f"Game already exists with externalGameId: "
                    f"{schema.externalGameId} . Cannot update externalGameId"
                )
        is_matching = are_variables_matching(schema.dict(), game.dict())
        params_schema = schema.dict().get("params", None)
        params_game = game.dict().get("params", None)
        params_is_matching = False
        if params_schema and params_game:
            params_is_matching = are_variables_matching(params_schema, params_game)

        if is_matching and params_is_matching:
            raise ConflictError(
                detail=("It is not possible to update the game with the same data")
            )
        if schema.dict() == game.dict():
            raise ConflictError(detail="No difference between schema and game")

        strategyId = schema.strategyId
        if strategyId:
            strategies = all_engine_strategies()
            strategy = next(
                (strategy for strategy in strategies if strategy.id == strategyId), None
            )
            if not strategy:
                raise NotFoundError(detail=f"Strategy with id: {strategyId} not found")
        if not strategyId:
            strategyId = game.strategyId
        if not strategyId:
            strategyId = "default"

        schema.strategyId = strategyId
        params = schema.params
        del schema.params
        updated_params = []
        if params:
            for param in params:
                self.game_params_repository.patch_game_params_by_id(param.id, param)
                updated_params.append(param)

        game = self.game_repository.patch_game_by_id(gameId, schema)
        game_dict = game.dict()
        response = ResponsePatchGame(
            externalGameId=game_dict["externalGameId"],
            strategyId=strategyId,
            platform=game_dict["platform"],
            params=updated_params,
            gameId=gameId,
            message=f"Game with gameId: {gameId} updated successfully",
        )
        return response

    def get_strategy_by_externalGameId(self, externalGameId: str):
        """
        Retrieves the strategy associated with a game by its external game ID.

        Args:
            externalGameId (str): The external game ID.

        Returns:
            dict: The strategy details.
        """
        game = self.game_repository.read_by_column(
            "externalGameId", externalGameId, not_found_raise_exception=True
        )

        if not game:
            raise NotFoundError(
                detail=f"Game not found by externalGameId: {externalGameId}"
            )

        return self.get_strategy_by_gameId(game.id)

    def get_strategy_by_gameId(self, gameId: UUID):
        """
        Retrieves the strategy associated with a game by its game ID.

        Args:
            gameId (UUID): The game ID.

        Returns:
            dict: The strategy details.
        """
        game = self.game_repository.read_by_id(gameId, not_found_raise_exception=False)
        if not game:
            raise NotFoundError(detail=f"Game not found by gameId: {gameId}")

        if not game.strategyId:
            raise ConflictError(
                detail=f"Game with gameId: {gameId} does not have a strategyId"
            )

        strategy = self.strategy_service.get_strategy_by_id(game.strategyId)
        game_params = self.game_params_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )

        if game_params:
            for param in game_params:
                if param.key in strategy["variables"]:
                    try:
                        param.value = int(param.value)
                    except ValueError:
                        try:
                            param.value = float(param.value)
                        except ValueError:
                            pass
                    type_param = type(param.value)
                    type_strategy_variable = type(strategy["variables"][param.key])
                    if type_param == type_strategy_variable:
                        strategy["variables"][param.key] = param.value

        strategy["game_params"] = game_params

        return strategy

    def get_tasks_by_gameId(self, gameId: UUID):
        """
        Retrieves the tasks associated with a game by its game ID.

        Args:
            gameId (UUID): The game ID.

        Returns:
            dict: The game details including tasks.
        """
        game = self.game_repository.read_by_id(gameId)
        if not game:
            raise NotFoundError(detail=f"Game not found by id: {gameId}")

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
