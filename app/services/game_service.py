from typing import Any, Optional
from uuid import UUID

from app.core.exceptions import (BadRequestError, ConflictError,
                                 NotFoundError)
from app.engine.all_engine_strategies import all_engine_strategies
from app.model.strategy_definition import StrategyDefinitionStatus
from app.repository.game_params_repository import GameParamsRepository
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.schema.games_params_schema import InsertGameParams
from app.schema.games_schema import (BaseGameResult, FindGameResult,
                                     GameCreated, PatchGame, PostCreateGame,
                                     ResponsePatchGame)
from app.services.base_service import BaseService
from app.services.game_access import get_authorized_game
from app.services.strategy_definition_service import \
    StrategyDefinitionService
from app.services.strategy_service import (StrategyService,
                                           is_custom_strategy_id,
                                           parse_custom_strategy_id,
                                           resolve_realm_id)
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
        user_points_repository: UserPointsRepository,
        strategy_service: StrategyService,
        strategy_definition_service: Optional[
            StrategyDefinitionService
        ] = None,
    ) -> None:
        """
        Initializes the GameService with the provided repositories and
          services.

        ``strategy_definition_service`` is optional so existing call sites
        and tests that don't exercise ``custom:`` strategyIds keep
        working; when omitted, attempting to PATCH a game with a
        ``custom:`` id raises a clear error instead of silently
        accepting it.
        """
        self.game_repository = game_repository
        self.game_params_repository = game_params_repository
        self.task_repository = task_repository
        self.strategy_service = strategy_service
        self.strategy_definition_service = strategy_definition_service
        super().__init__(game_repository)

    async def get_by_gameId(
        self,
        gameId: UUID,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> BaseGameResult:
        """
        Retrieves a game by its game ID.

        Args:
            gameId (UUID): The game ID.

        Returns:
            BaseGameResult: The game details.
        """
        if enforce_scope:
            response = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            response = await self.game_repository.read_by_column(
                "id",
                gameId,
                not_found_raise_exception=True,
                only_one=True,
                not_found_message=f"Game not found by gameId: {gameId}",
            )
        params = await self.game_params_repository.read_by_column(
            "gameId", response.id, not_found_raise_exception=False, only_one=False
        )
        response_dict = response.model_dump()
        response_dict["params"] = params

        response = BaseGameResult(**response_dict, gameId=gameId)

        return response

    async def delete_game_by_id(
        self,
        gameId: UUID,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> BaseGameResult | dict[str, str]:
        """
        Deletes a game by its game ID.

        Args:
            gameId (UUID): The game ID.

        Raises:
            NotFoundError: If the game is not found.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_id(
                gameId, not_found_raise_exception=False
            )
        if not game:
            raise NotFoundError(detail=f"Game not found by gameId: {gameId}")

        if await self.game_repository.delete_game_by_id(gameId):
            response = BaseGameResult(
                externalGameId=game.externalGameId,
                strategyId=game.strategyId,
                platform=game.platform,
                gameId=gameId,
                created_at=game.created_at,
                updated_at=game.updated_at,
                params=[],
                message=f"Game with gameId: {gameId} deleted successfully",
            )
            return response
        return {"message": f"Game with gameId: {gameId} not deleted"}

    async def get_all_games(
        self,
        schema,
        api_key=None,
        oauth_user_id=None,
        is_admin: bool = False,
    ) -> FindGameResult:
        """
        Retrieves all games based on the provided schema.

        Args:
            schema: The schema for filtering the games.
            api_key (str): The API key.

        Returns:
            list: A list of all games matching the schema.
        """
        return await self.game_repository.get_all_games(
            schema,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
            is_admin=is_admin,
        )

    async def get_by_externalId(self, externalGameId: str) -> Any:
        """
        Retrieves a game by its external game ID.

        Args:
            externalGameId (str): The external game ID.

        Returns:
            object: The game details.
        """
        return await self.game_repository.read_by_column("externalGameId", externalGameId)

    async def create(
        self, schema: PostCreateGame, api_key: str = None, oauth_user_id=None
    ) -> GameCreated:
        """
        Creates a new game using the provided schema.

        Args:
            schema (PostCreateGame): The schema representing the game to be
              created.
            api_key (str): The API key.
            oauth_user_id (str): The OAuth user ID.

        Returns:
            GameCreated: The created game details.
        """
        params = schema.params
        externalGameId = schema.externalGameId

        externalGameId_exist = await self.game_repository.read_by_column(
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
                detail={
                    "message": f"Game already exists with externalGameId: "
                    f"{externalGameId}",
                    "gameId": str(externalGameId_exist.id),
                }
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

        if api_key:
            schema.apiKey_used = api_key

        if oauth_user_id:
            schema.oauth_user_id = oauth_user_id
        game = await self.game_repository.create(schema)
        if params:
            del schema.params

            for param in params:
                params_dict = param.model_dump()
                params_dict["gameId"] = str(game.id)
                if api_key:
                    params_dict["apiKey_used"] = api_key
                if oauth_user_id:
                    params_dict["oauth_user_id"] = oauth_user_id
                params_to_insert = InsertGameParams(**params_dict)
                created_param = await self.game_params_repository.create(
                    params_to_insert
                )
                created_params.append(created_param)

        response = GameCreated(
            **game.model_dump(),
            params=created_params,
            gameId=game.id,
            message=f"Game with gameId: {game.id} created successfully",
        )
        return response

    async def _validate_strategy_assignment(
        self,
        strategy_id: str,
        *,
        api_key: Optional[str] = None,
        oauth_user_id: Optional[str] = None,
    ) -> None:
        """
        Validate a ``strategyId`` before persisting it onto a Game or Task.

        Two paths:
          * Built-in id (no ``custom:`` prefix): must resolve in the
            in-process registry (legacy behaviour).
          * ``custom:<uuid>``: must resolve in the DB-backed
            ``strategydefinition`` table, scoped to the caller's tenant,
            and must be PUBLISHED. We refuse DRAFT/ARCHIVED to avoid
            assigning a strategy that the resolver can't execute (DRAFT
            never runs; ARCHIVED would only run by accident if a prior
            rollback left dangling references — which the Sprint 9
            cascade is precisely designed to prevent).

        Raises ``NotFoundError`` for unknown ids, ``BadRequestError`` for
        not-yet-published customs.
        """
        if not is_custom_strategy_id(strategy_id):
            strategies = all_engine_strategies()
            strategy = next(
                (s for s in strategies if s.id == strategy_id), None
            )
            if not strategy:
                raise NotFoundError(
                    detail=f"Strategy with id: {strategy_id} not found"
                )
            return

        if self.strategy_definition_service is None:
            raise BadRequestError(
                detail=(
                    "Custom strategy assignment is unavailable: "
                    "StrategyDefinitionService not wired."
                )
            )
        realmId = resolve_realm_id(
            api_key=api_key, oauth_user_id=oauth_user_id
        )
        uuid_part = parse_custom_strategy_id(strategy_id)
        definition = await self.strategy_definition_service.get_strategy(
            id=uuid_part, realmId=realmId
        )
        if definition.status != StrategyDefinitionStatus.PUBLISHED.value:
            raise BadRequestError(
                detail=(
                    f"Only PUBLISHED custom strategies can be assigned. "
                    f"Strategy '{definition.name}' v{definition.version} "
                    f"is {definition.status}."
                )
            )

    async def patch_game_by_externalGameId(
        self, externalGameId: str, schema: PatchGame
    ) -> ResponsePatchGame:
        """
        Updates a game by its external game ID using the provided schema.

        Args:
            externalGameId (str): The external game ID.
            schema (PatchGame): The schema representing the updated data.

        Returns:
            ResponsePatchGame: The updated game details.
        """
        game = await self.game_repository.read_by_column(
            "externalGameId", externalGameId, not_found_raise_exception=False
        )
        if not game:
            raise NotFoundError(
                detail=f"Game not found by externalGameId: {externalGameId}"
            )
        return await self.patch_game_by_id(game.id, schema)

    async def patch_game_by_id(
        self,
        gameId: UUID,
        schema: PatchGame,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> ResponsePatchGame:
        """
        Updates a game by its game ID using the provided schema.

        Args:
            gameId (UUID): The game ID.
            schema (PatchGame): The schema representing the updated data.

        Returns:
            ResponsePatchGame: The updated game details.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_id(
                gameId, not_found_raise_exception=False
            )
        if not game:
            raise NotFoundError(detail=f"Game not found by gameId: {gameId}")
        if schema.externalGameId and schema.externalGameId != game.externalGameId:
            externalGameId_exist = await self.game_repository.read_by_column(
                "externalGameId", schema.externalGameId, not_found_raise_exception=False
            )
            if externalGameId_exist:
                raise ConflictError(
                    detail=f"Game already exists with externalGameId: "
                    f"{schema.externalGameId} . Cannot update externalGameId"
                )
        is_matching = are_variables_matching(schema.model_dump(), game.model_dump())
        params_schema = schema.model_dump().get("params", None)
        params_game = game.model_dump().get("params", None)
        params_is_matching = False
        if params_schema and params_game:
            params_is_matching = are_variables_matching(params_schema, params_game)

        if is_matching and params_is_matching:
            raise ConflictError(
                detail=("It is not possible to update the game with the same data")
            )
        if schema.model_dump() == game.model_dump():
            raise ConflictError(detail="No difference between schema and game")

        strategyId = schema.strategyId
        if strategyId:
            await self._validate_strategy_assignment(
                strategyId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
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
                await self.game_params_repository.patch_game_params_by_id(param.id, param)
                updated_params.append(param)

        game = await self.game_repository.patch_game_by_id(gameId, schema)
        game_dict = game.model_dump()
        response = ResponsePatchGame(
            externalGameId=game_dict["externalGameId"],
            strategyId=strategyId,
            platform=game_dict["platform"],
            params=updated_params,
            gameId=gameId,
            message=f"Game with gameId: {gameId} updated successfully",
        )
        return response

    async def get_strategy_by_externalGameId(
        self, externalGameId: str
    ) -> dict[str, Any]:
        """
        Retrieves the strategy associated with a game by its external game ID.

        Args:
            externalGameId (str): The external game ID.

        Returns:
            dict: The strategy details.
        """
        game = await self.game_repository.read_by_column(
            "externalGameId", externalGameId, not_found_raise_exception=True
        )

        if not game:
            raise NotFoundError(
                detail=f"Game not found by externalGameId: {externalGameId}"
            )

        return await self.get_strategy_by_gameId(game.id)

    async def get_strategy_by_gameId(
        self,
        gameId: UUID,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> dict[str, Any]:
        """
        Retrieves the strategy associated with a game by its game ID.

        Args:
            gameId (UUID): The game ID.

        Returns:
            dict: The strategy details.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_id(
                gameId, not_found_raise_exception=False
            )
        if not game:
            raise NotFoundError(detail=f"Game not found by gameId: {gameId}")

        if not game.strategyId:
            raise ConflictError(
                detail=f"Game with gameId: {gameId} does not have a strategyId"
            )

        strategy = self.strategy_service.get_strategy_by_id(game.strategyId)
        game_params = await self.game_params_repository.read_by_column(
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

    async def get_tasks_by_gameId(
        self,
        gameId: UUID,
        *,
        api_key: str = None,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> dict[str, Any]:
        """
        Retrieves the tasks associated with a game by its game ID.

        Args:
            gameId (UUID): The game ID.

        Returns:
            dict: The game details including tasks.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_id(gameId)
        if not game:
            raise NotFoundError(detail=f"Game not found by id: {gameId}")

        tasks = await self.task_repository.read_by_column(
            "gameId", gameId, not_found_raise_exception=False, only_one=False
        )
        tasks_list = []
        if tasks:
            for task in tasks:
                tasks_list.append(task.model_dump())
        game_dict = game.model_dump()
        game_dict["tasks"] = tasks_list

        return game_dict

    async def get_game_by_external_id(
        self, externalGameId: str, api_key: str = None, oauth_user_id=None
    ) -> Any:
        """
        Retrieves a game by its external game ID.

        Args:
            externalGameId (str): The external game ID.
            api_key (str): The API key.
            oauth_user_id (str): The OAuth user ID.

        Returns:
            dict: The game details.
        """
        game = await self.game_repository.read_by_column(
            "externalGameId", externalGameId, not_found_raise_exception=False
        )
        if not game:
            raise NotFoundError(
                detail=f"Game not found by externalGameId: {externalGameId}"
            )

        if api_key:
            game.apiKey_used = api_key
        if oauth_user_id:
            game.oauth_user_id = oauth_user_id

        return game
