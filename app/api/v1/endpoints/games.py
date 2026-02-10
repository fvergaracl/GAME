from typing import List
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends

from app.core.config import configs
from app.core.container import Container
from app.core.exceptions import ForbiddenError, InternalServerError
from app.middlewares.authentication import auth_api_key_or_oauth2, auth_oauth2
from app.middlewares.valid_access_token import oauth_2_scheme, valid_access_token
from app.schema.games_schema import (BaseGameResult, FindGameResult, GameCreated,
                                     ListTasksWithUsers, PatchGame, PostCreateGame,
                                     PostFindGame, ResponsePatchGame)
from app.schema.oauth_users_schema import CreateOAuthUser
from app.schema.strategy_schema import Strategy
from app.schema.task_schema import (AddActionDidByUserInTask,
                                    AsignPointsToExternalUserId,
                                    AssignedPointsToExternalUserId, CreateTaskPost,
                                    CreateTaskPostSuccesfullyCreated, CreateTasksPost,
                                    CreateTasksPostBulkCreated, FoundTasks,
                                    PostFindTask, ResponseAddActionDidByUserInTask,
                                    SimulatedPointsAssignedToUser)
from app.schema.user_points_schema import (AllPointsByGame, AllPointsByGameWithDetails,
                                           PointsAssignedToUser)
from app.services.apikey_service import ApiKeyService
from app.services.game_service import GameService
from app.services.logs_service import LogsService
from app.services.oauth_users_service import OAuthUsersService
from app.services.task_service import TaskService
from app.services.user_actions_service import UserActionsService
from app.services.user_points_service import UserPointsService
from app.services.user_service import UserService
from app.util.add_log import add_log
from app.util.calculate_hash_simulated_strategy import calculate_hash_simulated_strategy
from app.util.check_role import check_role

router = APIRouter(
    prefix="/games",
    tags=["games"],
)

summary_get_games_list = "Retrieve All Games"
response_example_get_games_list = {
    "items": [
        {
            "gameId": "4ce32be2-77f6-4ffc-8e07-78dc220f0520",
            "created_at": "2026-02-10T12:15:00Z",
            "updated_at": "2026-02-10T12:15:00Z",
            "externalGameId": "game-readme-001",
            "strategyId": "default",
            "platform": "web",
            "params": [
                {
                    "id": "fd8551f4-7cf0-4f8b-b372-a269541db5a5",
                    "key": "variable_basic_points",
                    "value": 10,
                }
            ],
        }
    ],
    "search_options": {
        "ordering": "-id",
        "page": 1,
        "page_size": 10,
        "total_count": 1,
    },
}

responses_get_games_list = {
    200: {
        "description": "Games retrieved successfully",
        "content": {"application/json": {"example": response_example_get_games_list}},
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    422: {
        "description": "Validation error in query parameters",
    },
    500: {
        "description": "Internal server error while retrieving games",
    },
}

description_get_games_list = """
Returns a paginated list of games and their effective configuration parameters.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.
- If an admin bearer token is provided (`AdministratorGAME`), all games can be listed.
- If API key is used, results are scoped according to the key permissions.

### Query Parameters
- `externalGameId` (`string`, optional): Filter by external game identifier.
- `platform` (`string`, optional): Filter by platform (for example: `web`, `mobile`).
- `ordering` (`string`, optional): Sort expression (for example: `-id`, `created_at`).
- `page` (`integer`, optional): Result page number.
- `page_size` (`integer|string`, optional): Number of items per page.

### Success (200)
Returns:
- `items`: list of games
- `search_options`: pagination/filter metadata

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `422`: invalid query parameters
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_games_list`</sub>
"""  # noqa


@router.get(
    "",
    response_model=FindGameResult,
    description=description_get_games_list,
    summary=summary_get_games_list,
    responses=responses_get_games_list,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_games_list(
    schema: PostFindGame = Depends(),
    service: GameService = Depends(Provide[Container.game_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve a list of all games with their parameters.

    Args:
        schema(PostFindGame): Query parameters for finding games.
        service(GameService): Injected GameService dependency.
        service_log(LogsService): Injected LogsService dependency.
        service_oauth(OAuthUsersService): Injected OAuthUsersService dependency.
        token(str): The OAuth2 token.
        api_key_header(str): The API key header.


    Returns:
        FindGameResult: A result set containing the games and search options.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        token_data = token_data.data
        oauth_user_id = token_data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Get games list - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
        is_admin = check_role(token_data, "AdministratorGAME")
        if is_admin:
            return service.get_all_games(schema)
    await add_log(
        "game",
        "INFO",
        "Game list retrieval",
        schema.dict(),
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_all_games(schema, api_key)


summary_get_game_by_id = "Retrieve Game by ID"
response_example_get_game_by_id = {
    "gameId": "4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    "created_at": "2026-02-10T12:15:00Z",
    "updated_at": "2026-02-10T12:15:00Z",
    "externalGameId": "game-readme-001",
    "strategyId": "default",
    "platform": "web",
    "params": [
        {
            "id": "fd8551f4-7cf0-4f8b-b372-a269541db5a5",
            "key": "variable_basic_points",
            "value": 10,
        }
    ],
}

responses_get_game_by_id = {
    200: {
        "description": "Game retrieved successfully",
        "content": {"application/json": {"example": response_example_get_game_by_id}},
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game not found for the provided id",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find item with gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
    },
    500: {
        "description": "Internal server error while retrieving game",
    },
}

description_get_game_by_id = """
Returns one game and its effective configuration parameters by internal `gameId`.

### Path Parameter
- `gameId` (`UUID`, required): Internal game identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns the game metadata and strategy parameters:
- `gameId`
- `externalGameId`
- `strategyId`
- `platform`
- `params`
- `created_at`
- `updated_at`

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: no game found with the provided `gameId`
- `422`: malformed `gameId` (invalid UUID format)
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_game_by_id`</sub>
"""  # noqa


@router.get(
    "/{gameId}",
    response_model=BaseGameResult,
    description=description_get_game_by_id,
    summary=summary_get_game_by_id,
    responses=responses_get_game_by_id,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_game_by_id(
    gameId: UUID,
    service: GameService = Depends(Provide[Container.game_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve a game by its ID.

    Args:
        gameId(UUID): The ID of the game.
        service(GameService): Injected GameService dependency.
        service_log(LogsService): Injected LogsService dependency.
        service_oauth(OAuthUsersService): Injected OAuthUsersService dependency.
        token(str): The OAuth2 token.
        api_key_header(str): The API key header.

    Returns:
        BaseGameResult: The details of the specified game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Get game by ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Game retrieval by ID",
        {"gameId": str(gameId)},
        service_log,
        api_key,
        oauth_user_id,
    )
    response = service.get_by_gameId(gameId)
    return response


# delete game by gameId
summary_delete_game_by_id = "Delete Game by ID"
response_example_delete_game_by_id = {
    "gameId": "4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    "created_at": "2026-02-10T12:15:00Z",
    "updated_at": "2026-02-10T12:15:00Z",
    "externalGameId": "game-readme-001",
    "strategyId": "default",
    "platform": "web",
    "params": [
        {
            "id": "fd8551f4-7cf0-4f8b-b372-a269541db5a5",
            "key": "variable_basic_points",
            "value": 10,
        }
    ],
}

responses_delete_game_by_id = {
    200: {
        "description": "Game deleted successfully",
        "content": {"application/json": {"example": response_example_delete_game_by_id}},
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game not found for the provided id",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find item with gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
    },
    500: {
        "description": "Internal server error while deleting game",
    },
}

description_delete_game_by_id = """
Deletes one game by internal `gameId` and returns the deleted resource payload.

### Path Parameter
- `gameId` (`UUID`, required): Internal game identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns the deleted game metadata:
- `gameId`
- `externalGameId`
- `strategyId`
- `platform`
- `params`
- `created_at`
- `updated_at`

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: no game found with the provided `gameId`
- `422`: malformed `gameId` (invalid UUID format)
- `500`: deletion failure

<sub>**Id_endpoint:** `delete_game_by_id`</sub>
"""  # noqa


@router.delete(
    "/{gameId}",
    response_model=BaseGameResult,
    description=description_delete_game_by_id,
    summary=summary_delete_game_by_id,
    responses=responses_delete_game_by_id,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def delete_game_by_id(
    gameId: UUID,
    service: GameService = Depends(Provide[Container.game_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Delete a game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (GameService): Injected GameService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        BaseGameResult: The details of the deleted game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Delete game by ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )

    await add_log(
        "game",
        "INFO",
        "Game deletion by ID",
        {"gameId": str(gameId)},
        service_log,
        api_key,
        oauth_user_id,
    )

    try:
        response = service.delete_game_by_id(gameId)
        data_to_log = {"gameId": str(gameId)}
        await add_log(
            "game",
            "SUCCESS",
            "Game deletion successful",
            data_to_log,
            service_log,
            api_key,
            oauth_user_id,
        )
        return response
    except Exception as e:
        await add_log(
            "game",
            "ERROR",
            "Game deletion failed",
            {"error": str(e)},
            service_log,
            api_key,
            oauth_user_id,
        )
        raise e


summary_create_game = "Create a New Game"
request_example_create_game = {
    "externalGameId": "game-readme-001",
    "platform": "web",
    "strategyId": "default",
    "params": [
        {
            "key": "variable_basic_points",
            "value": 10,
        }
    ],
}

response_example_create_game = {
    "gameId": "4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    "created_at": "2026-02-10T12:15:00Z",
    "updated_at": "2026-02-10T12:15:00Z",
    "externalGameId": "game-readme-001",
    "strategyId": "default",
    "platform": "web",
    "params": [
        {
            "id": "fd8551f4-7cf0-4f8b-b372-a269541db5a5",
            "key": "variable_basic_points",
            "value": 10,
        }
    ],
    "message": "Successfully created",
}

responses_create_game = {
    200: {
        "description": "Game created successfully",
        "content": {"application/json": {"example": response_example_create_game}},
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    422: {
        "description": "Validation error in request payload",
    },
    500: {
        "description": "Internal server error while creating game",
    },
}

description_create_game = """
Creates a new game and persists its strategy configuration.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.
- Admin bearer tokens can create games without API-key scoping.

### Request Body
- `externalGameId` (`string`, required): external identifier used by the client system.
- `platform` (`string`, required): target platform (for example: `web`, `mobile`).
- `strategyId` (`string`, optional): strategy identifier (`default` if omitted).
- `params` (`array`, optional): key/value game parameters consumed by strategy logic.

### Success (200)
Returns the created game metadata and persisted parameters.

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `422`: invalid request payload
- `500`: creation failure

<sub>**Id_endpoint:** `create_game`</sub>
"""  # noqa


@router.post(
    "",
    response_model=GameCreated,
    summary=summary_create_game,
    description=description_create_game,
    responses=responses_create_game,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def create_game(
    schema: PostCreateGame = Body(..., example=request_example_create_game),
    service: GameService = Depends(Provide[Container.game_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Create a new game.

    Args:
        schema (PostCreateGame): The schema for creating a new game.
        service (GameService): Injected GameService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        api_key_header (str): The API key header.

    Returns:
        GameCreated: The details of the created game.
    """

    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Create game - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Game creation",
        schema.dict(),
        service_log,
        api_key,
        oauth_user_id,
    )
    try:
        response = await service.create(schema, api_key, oauth_user_id)
        data_to_log = {"body": schema.dict(), "gameId": str(response.gameId)}
        await add_log(
            "game",
            "SUCCESS",
            "Game creation successful",
            data_to_log,
            service_log,
            api_key,
            oauth_user_id,
        )
        return response
    except Exception as e:
        await add_log(
            "game",
            "ERROR",
            "Game creation failed",
            {"error": str(e)},
            service_log,
            api_key,
            oauth_user_id,
        )
        raise e


summary_patch_game = "Update Game Details"
request_example_patch_game = {
    "externalGameId": "game-readme-001-updated",
    "strategyId": "default",
    "platform": "mobile",
    "params": [
        {
            "id": "fd8551f4-7cf0-4f8b-b372-a269541db5a5",
            "key": "variable_basic_points",
            "value": 15,
        }
    ],
}

response_example_patch_game = {
    "externalGameId": "game-readme-001-updated",
    "strategyId": "default",
    "platform": "mobile",
    "params": [
        {
            "id": "fd8551f4-7cf0-4f8b-b372-a269541db5a5",
            "key": "variable_basic_points",
            "value": 15,
        }
    ],
    "message": "Successfully updated",
}

responses_patch_game = {
    200: {
        "description": "Game updated successfully",
        "content": {"application/json": {"example": response_example_patch_game}},
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game not found for the provided id",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find item with gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path/body payload",
    },
    500: {
        "description": "Internal server error while updating game",
    },
}

description_patch_game = """
Partially updates game fields and/or game parameters for the provided `gameId`.

### Path Parameter
- `gameId` (`UUID`, required): Internal game identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Request Body
Any subset of:
- `externalGameId` (`string`)
- `strategyId` (`string`)
- `platform` (`string`)
- `params` (`array` of `{id, key, value}`) for parameter updates

### Success (200)
Returns the updated game fields plus `message`.

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: no game found with the provided `gameId`
- `422`: malformed UUID or invalid patch body
- `500`: update failure

<sub>**Id_endpoint:** `patch_game`</sub>
"""  # noqa


@router.patch(
    "/{gameId}",
    response_model=ResponsePatchGame,
    summary=summary_patch_game,
    description=description_patch_game,
    responses=responses_patch_game,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def patch_game(
    gameId: UUID,
    schema: PatchGame = Body(..., example=request_example_patch_game),
    service: GameService = Depends(Provide[Container.game_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Update a game by its ID.

    Args:
        gameId (UUID): The ID of the game to update.
        schema (PatchGame): The schema for updating the game.
        service (GameService): Injected GameService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ResponsePatchGame: The updated game details.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Update game by ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Game update by ID",
        {"gameId": str(gameId), "body": schema.dict()},
        service_log,
        api_key,
        oauth_user_id,
    )

    try:
        response = await service.patch_game_by_id(gameId, schema)
        data_to_log = {"gameId": str(gameId), "body": schema.dict()}
        await add_log(
            "game",
            "SUCCESS",
            "Game update successful",
            data_to_log,
            service_log,
            api_key,
            oauth_user_id,
        )
        return response
    except Exception as e:
        await add_log(
            "game",
            "ERROR",
            "Game update failed",
            {"error": str(e)},
            service_log,
            api_key,
            oauth_user_id,
        )
        raise e


summary_get_strategy_by_gameId = "Retrieve Strategy by Game ID"
response_example_get_strategy_by_gameId = {
    "id": "default",
    "name": "Default Strategy",
    "description": "Baseline adaptive scoring strategy.",
    "version": "1.0.0",
    "variables": {
        "variable_basic_points": 10,
        "bonus_multiplier": 1.2,
    },
    "hash_version": "9e6c5ce8f3fcb2a4f6b5b2f1c1d2a9f7",
}

responses_get_strategy_by_gameId = {
    200: {
        "description": "Strategy associated with the game retrieved successfully",
        "content": {
            "application/json": {"example": response_example_get_strategy_by_gameId}
        },
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game or strategy not found for the provided id",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find strategy for gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
    },
    500: {
        "description": "Internal server error while retrieving game strategy",
    },
}

description_get_strategy_by_gameId = """
Returns the strategy currently linked to the provided `gameId`.

### Path Parameter
- `gameId` (`UUID`, required): Internal game identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns the effective strategy object:
- `id`
- `name`
- `description`
- `version`
- `variables`
- `hash_version`

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: game not found or strategy unavailable
- `422`: malformed `gameId` (invalid UUID format)
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_strategy_by_gameId`</sub>
"""  # noqa


@router.get(
    "/{gameId}/strategy",
    response_model=Strategy,
    summary=summary_get_strategy_by_gameId,
    description=description_get_strategy_by_gameId,
    responses=responses_get_strategy_by_gameId,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_strategy_by_gameId(
    gameId: UUID,
    service: GameService = Depends(Provide[Container.game_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve the strategy associated with a game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (GameService): Injected GameService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        Strategy: The strategy associated with the specified game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Get strategy by game ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Strategy retrieval by game ID",
        {"gameId": str(gameId)},
        service_log,
        api_key,
        oauth_user_id,
    )

    return service.get_strategy_by_gameId(gameId)


summary_create_task = "Create a New Task"
request_example_create_task = {
    "externalTaskId": "task-login",
    "strategyId": "default",
    "params": [
        {
            "key": "variable_bonus_points",
            "value": 20,
        }
    ],
}

response_example_create_task = {
    "message": "Successfully created",
    "id": "9ea6a77d-b540-4548-8f76-f23f3dce56bd",
    "created_at": "2026-02-10T12:20:00Z",
    "updated_at": "2026-02-10T12:20:00Z",
    "externalTaskId": "task-login",
    "externalGameId": "game-readme-001",
    "gameParams": [
        {
            "key": "variable_basic_points",
            "value": 10,
        }
    ],
    "taskParams": [
        {
            "key": "variable_bonus_points",
            "value": 20,
        }
    ],
    "strategy": {
        "id": "default",
        "name": "Default Strategy",
        "description": "Baseline adaptive scoring strategy.",
        "version": "1.0.0",
        "variables": {
            "variable_basic_points": 10,
            "bonus_multiplier": 1.2,
        },
        "hash_version": "9e6c5ce8f3fcb2a4f6b5b2f1c1d2a9f7",
    },
}

responses_create_task = {
    200: {
        "description": "Task created successfully",
        "content": {"application/json": {"example": response_example_create_task}},
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game not found for the provided id",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find item with gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path/body payload",
    },
    500: {
        "description": "Internal server error while creating task",
    },
}

description_create_task = """
Creates a new task linked to an existing game.

### Path Parameter
- `gameId` (`UUID`, required): Internal game identifier where the task will be created.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Request Body
- `externalTaskId` (`string`, required): External task identifier from the client domain.
- `strategyId` (`string`, optional): Strategy override for this task. If omitted, inheritance rules apply.
- `params` (`array`, optional): Task-level key/value parameters used during scoring.

### Success (200)
Returns created task metadata with inherited game params, task params, and effective strategy.

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: no game found with the provided `gameId`
- `422`: malformed UUID or invalid request payload
- `500`: creation failure

<sub>**Id_endpoint:** `create_task`</sub>
"""  # noqa


@router.post(
    "/{gameId}/tasks",
    response_model=CreateTaskPostSuccesfullyCreated,
    summary=summary_create_task,
    description=description_create_task,
    responses=responses_create_task,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def create_task(
    gameId: UUID,
    create_query: CreateTaskPost = Body(..., example=request_example_create_task),
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Create a task for a specific game.

    Args:
        gameId (UUID): The ID of the game.
        create_query (CreateTaskPost): The schema for creating a task.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        CreateTaskPostSuccesfullyCreated: The details of the created task.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Create task - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Task creation",
        {"gameId": str(gameId), "body": create_query.dict()},
        service_log,
        api_key,
        oauth_user_id,
    )
    try:
        response = await service.create_task_by_game_id(gameId, create_query, api_key)
        data_to_log = {"gameId": str(gameId), "body": create_query.dict()}
        await add_log(
            "game",
            "SUCCESS",
            "Task creation successful",
            data_to_log,
            service_log,
            api_key,
            oauth_user_id,
        )
        return response
    except Exception as e:
        await add_log(
            "game",
            "ERROR",
            "Task creation failed",
            {"error": str(e)},
            service_log,
            api_key,
            oauth_user_id,
        )
        raise e


summary_create_tasks_bulk = "Create Multiple New Tasks"
request_example_create_tasks_bulk = {
    "tasks": [
        {
            "externalTaskId": "task-login",
            "strategyId": "default",
            "params": [
                {
                    "key": "variable_bonus_points",
                    "value": 20,
                }
            ],
        },
        {
            "externalTaskId": "task-share",
            "strategyId": "default",
            "params": [
                {
                    "key": "variable_bonus_points",
                    "value": 30,
                }
            ],
        },
    ]
}

response_example_create_tasks_bulk = {
    "succesfully_created": [
        {
            "message": "Successfully created",
            "id": "9ea6a77d-b540-4548-8f76-f23f3dce56bd",
            "created_at": "2026-02-10T12:20:00Z",
            "updated_at": "2026-02-10T12:20:00Z",
            "externalTaskId": "task-login",
            "externalGameId": "game-readme-001",
            "gameParams": [
                {
                    "key": "variable_basic_points",
                    "value": 10,
                }
            ],
            "taskParams": [
                {
                    "key": "variable_bonus_points",
                    "value": 20,
                }
            ],
            "strategy": {
                "id": "default",
                "name": "Default Strategy",
                "description": "Baseline adaptive scoring strategy.",
                "version": "1.0.0",
                "variables": {
                    "variable_basic_points": 10,
                    "bonus_multiplier": 1.2,
                },
                "hash_version": "9e6c5ce8f3fcb2a4f6b5b2f1c1d2a9f7",
            },
        }
    ],
    "failed_to_create": [
        {
            "task": {
                "externalTaskId": "task-share",
                "strategyId": "default",
                "params": [
                    {
                        "key": "variable_bonus_points",
                        "value": 30,
                    }
                ],
            },
            "error": "Task already exists for externalTaskId=task-share",
        }
    ],
}

responses_create_tasks_bulk = {
    200: {
        "description": "Bulk task creation processed (can contain both successes and failures)",
        "content": {"application/json": {"example": response_example_create_tasks_bulk}},
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game not found for the provided id",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find item with gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path/body payload",
    },
    500: {
        "description": "Internal server error while processing bulk creation",
    },
}

description_create_tasks_bulk = """
Creates multiple tasks in one request for a specific game.

### Path Parameter
- `gameId` (`UUID`, required): Internal game identifier where tasks will be created.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Request Body
- `tasks` (`array`, required): list of task payloads.
- Each task accepts:
  - `externalTaskId` (`string`, required)
  - `strategyId` (`string`, optional)
  - `params` (`array`, optional)

### Success (200)
Returns a mixed outcome payload:
- `succesfully_created`: tasks created successfully
- `failed_to_create`: task payloads that failed with error reason

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: no game found with the provided `gameId`
- `422`: malformed UUID or invalid request payload
- `500`: bulk processing failure

<sub>**Id_endpoint:** `create_tasks_bulk`</sub>
"""  # noqa


@router.post(
    "/{gameId}/tasks/bulk",
    response_model=CreateTasksPostBulkCreated,
    summary=summary_create_tasks_bulk,
    description=description_create_tasks_bulk,
    responses=responses_create_tasks_bulk,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def create_tasks_bulk(
    gameId: UUID,
    create_query: CreateTasksPost = Body(..., example=request_example_create_tasks_bulk),
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Create multiple tasks for a specific game (bulk creation).

    Args:
        gameId (UUID): The ID of the game.
        create_query (CreateTasksPost): The schema for creating multiple tasks.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[CreateTaskPostSuccesfullyCreated]: The details of the created
          tasks.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Bulk task creation - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    succesfully_created = []
    failed_to_create = []
    await add_log(
        "game",
        "INFO",
        "Bulk task creation",
        {"gameId": str(gameId), "body": create_query.dict()},
        service_log,
        api_key,
        oauth_user_id,
    )

    for task in create_query.tasks:
        try:
            created_task = await service.create_task_by_game_id(gameId, task, api_key)
            succesfully_created.append(created_task)
        except Exception as e:
            failed_to_create.append({"task": task, "error": str(e)})
    if len(failed_to_create) > 0:
        await add_log(
            "game",
            "ERROR",
            "Bulk task creation failed",
            {
                "gameId": str(gameId),
                "body": create_query.dict(),
                "failed_tasks": failed_to_create,
            },
            service_log,
            api_key,
            oauth_user_id,
        )
    if len(succesfully_created) > 0:
        await add_log(
            "game",
            "SUCCESS",
            "Bulk task creation successful",
            {
                "gameId": str(gameId),
                "body": create_query.dict(),
                "succesfully_created": succesfully_created,
            },
            service_log,
            api_key,
            oauth_user_id,
        )

    return {
        "succesfully_created": succesfully_created,
        "failed_to_create": failed_to_create,
    }


summary_get_task_list = "Retrieve Task List"
response_example_get_task_list = {
    "items": [
        {
            "id": "9ea6a77d-b540-4548-8f76-f23f3dce56bd",
            "created_at": "2026-02-10T12:20:00Z",
            "updated_at": "2026-02-10T12:20:00Z",
            "externalTaskId": "task-login",
            "gameParams": [
                {
                    "key": "variable_basic_points",
                    "value": 10,
                }
            ],
            "taskParams": [
                {
                    "key": "variable_bonus_points",
                    "value": 20,
                }
            ],
            "strategy": {
                "id": "default",
                "name": "Default Strategy",
                "description": "Baseline adaptive scoring strategy.",
                "version": "1.0.0",
                "variables": {
                    "variable_basic_points": 10,
                    "bonus_multiplier": 1.2,
                },
                "hash_version": "9e6c5ce8f3fcb2a4f6b5b2f1c1d2a9f7",
            },
        }
    ],
    "search_options": {
        "ordering": "-id",
        "page": 1,
        "page_size": 10,
        "total_count": 1,
    },
}

responses_get_task_list = {
    200: {
        "description": "Task list retrieved successfully",
        "content": {"application/json": {"example": response_example_get_task_list}},
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game not found for the provided id",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find item with gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path/query parameters",
    },
    500: {
        "description": "Internal server error while retrieving task list",
    },
}

description_get_task_list = """
Returns a paginated list of tasks linked to a specific game.

### Path Parameter
- `gameId` (`UUID`, required): Internal game identifier.

### Query Parameters
- `ordering` (`string`, optional): Sort expression (for example: `-id`, `created_at`).
- `page` (`integer`, optional): Result page number.
- `page_size` (`integer|string`, optional): Number of items per page.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns:
- `items`: list of tasks with inherited game params, task params, and strategy metadata
- `search_options`: pagination/filter metadata

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: no game found with the provided `gameId`
- `422`: malformed UUID or invalid query params
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_task_list`</sub>
"""  # noqa


@router.get(
    "/{gameId}/tasks",
    response_model=FoundTasks,
    summary=summary_get_task_list,
    description=description_get_task_list,
    responses=responses_get_task_list,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_task_list(
    gameId: UUID,
    find_query: PostFindTask = Depends(),
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve a list of tasks for a specific game.

    Args:
        gameId (UUID): The ID of the game.
        find_query (PostFindTask): Query parameters for finding tasks.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        FoundTasks: A result set containing the tasks.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Task list retrieval - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Task list retrieval",
        {"gameId": str(gameId), "body": find_query.dict()},
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_tasks_list_by_gameId(gameId, find_query)


summary_get_task_by_gameId_taskId = (
    "Retrieve Task by Game ID and External Task ID"  # noqa
)
response_example_get_task_by_gameId_taskId = {
    "message": "Successfully created",
    "id": "9ea6a77d-b540-4548-8f76-f23f3dce56bd",
    "created_at": "2026-02-10T12:20:00Z",
    "updated_at": "2026-02-10T12:20:00Z",
    "externalTaskId": "task-login",
    "externalGameId": "game-readme-001",
    "gameParams": [
        {
            "key": "variable_basic_points",
            "value": 10,
        }
    ],
    "taskParams": [
        {
            "key": "variable_bonus_points",
            "value": 20,
        }
    ],
    "strategy": {
        "id": "default",
        "name": "Default Strategy",
        "description": "Baseline adaptive scoring strategy.",
        "version": "1.0.0",
        "variables": {
            "variable_basic_points": 10,
            "bonus_multiplier": 1.2,
        },
        "hash_version": "9e6c5ce8f3fcb2a4f6b5b2f1c1d2a9f7",
    },
}

responses_get_task_by_gameId_taskId = {
    200: {
        "description": "Task retrieved successfully",
        "content": {
            "application/json": {
                "example": response_example_get_task_by_gameId_taskId
            }
        },
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game or task not found for provided identifiers",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find task with externalTaskId = task-login for gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
    },
    500: {
        "description": "Internal server error while retrieving task",
    },
}

description_get_task_by_gameId_taskId = """
Returns one task identified by `gameId` + `externalTaskId`.

### Path Parameters
- `gameId` (`UUID`, required): Internal game identifier.
- `externalTaskId` (`string`, required): External task identifier in client domain.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns task metadata with:
- inherited game params
- task params
- effective strategy

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: game/task association not found
- `422`: malformed path parameters
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_task_by_gameId_taskId`</sub>
"""  # noqa


@router.get(
    "/{gameId}/tasks/{externalTaskId}",
    response_model=CreateTaskPostSuccesfullyCreated,
    summary=summary_get_task_by_gameId_taskId,
    description=description_get_task_by_gameId_taskId,
    responses=responses_get_task_by_gameId_taskId,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_task_by_gameId_taskId(
    gameId: UUID,
    externalTaskId: str,
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve a task by its external game ID and external task ID.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        CreateTaskPostSuccesfullyCreated: The details of the specified task.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Task retrieval by game ID and external task ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )

    await add_log(
        "game",
        "INFO",
        "Task retrieval by game ID and external task ID",
        {"gameId": str(gameId), "externalTaskId": externalTaskId},
        service_log,
        api_key,
        oauth_user_id,
    )

    return service.get_task_by_externalGameId_externalTaskId(
        str(gameId), externalTaskId
    )


summary_get_points_by_gameId = "Retrieve Points by Game ID"
response_example_get_points_by_gameId = {
    "externalGameId": "game-readme-001",
    "created_at": "2026-02-10T12:20:00Z",
    "task": [
        {
            "externalTaskId": "task-login",
            "points": [
                {
                    "externalUserId": "user-123",
                    "points": 120,
                    "timesAwarded": 6,
                },
                {
                    "externalUserId": "user-456",
                    "points": 40,
                    "timesAwarded": 2,
                },
            ],
        },
        {
            "externalTaskId": "task-share",
            "points": [
                {
                    "externalUserId": "user-123",
                    "points": 30,
                    "timesAwarded": 1,
                }
            ],
        },
    ],
}

responses_get_points_by_gameId = {
    200: {
        "description": "Points aggregated by game retrieved successfully",
        "content": {
            "application/json": {"example": response_example_get_points_by_gameId}
        },
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game not found for the provided id",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find item with gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
    },
    500: {
        "description": "Internal server error while retrieving game points",
    },
}

description_get_points_by_gameId = """
Returns game-level point aggregation grouped by task and user.

### Path Parameter
- `gameId` (`UUID`, required): Internal game identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns:
- `externalGameId`
- `created_at`
- `task`: list of tasks with points per user (`externalUserId`, `points`, `timesAwarded`)

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: no game found with the provided `gameId`
- `422`: malformed `gameId` (invalid UUID format)
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_points_by_gameId`</sub>
"""  # noqa


@router.get(
    "/{gameId}/points",
    response_model=AllPointsByGame,
    summary=summary_get_points_by_gameId,
    description=description_get_points_by_gameId,
    responses=responses_get_points_by_gameId,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_by_gameId(
    gameId: UUID,
    service: UserPointsService = Depends(Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve points associated with a specific game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        AllPointsByGame: The points details for the specified game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Points retrieval by game ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Points retrieval by game ID",
        {"gameId": str(gameId)},
        service_log,
        api_key,
        oauth_user_id,
    )

    return service.get_points_by_gameId(gameId)


summary_get_points_by_gameId_with_details = "Retrieve Points by Game ID with Details"
response_example_get_points_by_gameId_with_details = {
    "externalGameId": "game-readme-001",
    "created_at": "2026-02-10T12:20:00Z",
    "task": [
        {
            "externalTaskId": "task-login",
            "points": [
                {
                    "externalUserId": "user-123",
                    "points": 120,
                    "timesAwarded": 6,
                    "pointsData": [
                        {
                            "points": 20,
                            "caseName": "daily_login",
                            "created_at": "2026-02-10T08:00:00Z",
                        },
                        {
                            "points": 100,
                            "caseName": "weekly_bonus",
                            "created_at": "2026-02-10T12:00:00Z",
                        },
                    ],
                }
            ],
        }
    ],
}

responses_get_points_by_gameId_with_details = {
    200: {
        "description": "Detailed points by game retrieved successfully",
        "content": {
            "application/json": {
                "example": response_example_get_points_by_gameId_with_details
            }
        },
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game not found for the provided id",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find item with gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
    },
    500: {
        "description": "Internal server error while retrieving detailed points",
    },
}

description_get_points_by_gameId_with_details = """
Returns game-level point aggregation with per-award detail records.

### Path Parameter
- `gameId` (`UUID`, required): Internal game identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns:
- `externalGameId`
- `created_at`
- `task`: list of tasks with per-user totals and `pointsData` history (`points`, `caseName`, `created_at`)

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: no game found with the provided `gameId`
- `422`: malformed `gameId` (invalid UUID format)
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_points_by_gameId_with_details`</sub>
"""  # noqa


@router.get(
    "/{gameId}/points/details",
    response_model=AllPointsByGameWithDetails,
    summary=summary_get_points_by_gameId_with_details,
    description=description_get_points_by_gameId_with_details,
    responses=responses_get_points_by_gameId_with_details,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_by_gameId_with_details(
    gameId: UUID,
    service: UserPointsService = Depends(Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve points associated with a specific game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        AllPointsByGame: The points details for the specified game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Points retrieval by game ID with details - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Points retrieval by game ID with details",
        {"gameId": str(gameId)},
        service_log,
        api_key,
        oauth_user_id,
    )

    return service.get_points_by_gameId_with_details(gameId)


summary_get_points_of_user_in_game = "Retrieve User Points in Game"
response_example_get_points_of_user_in_game = [
    {
        "externalUserId": "user-123",
        "points": 120,
        "timesAwarded": 6,
    }
]

responses_get_points_of_user_in_game = {
    200: {
        "description": "User points in game retrieved successfully",
        "content": {
            "application/json": {
                "example": response_example_get_points_of_user_in_game
            }
        },
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game or user points not found",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find points for externalUserId = user-123 in gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
    },
    500: {
        "description": "Internal server error while retrieving user points in game",
    },
}

description_get_points_of_user_in_game = """
Returns point totals for one user within one game.

### Path Parameters
- `gameId` (`UUID`, required): Internal game identifier.
- `externalUserId` (`string`, required): External user identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns a list of point aggregates for the specified user in the game:
- `externalUserId`
- `points`
- `timesAwarded`

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: game/user points not found
- `422`: malformed path parameters
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_points_of_user_in_game`</sub>
"""  # noqa


@router.get(
    "/{gameId}/users/{externalUserId}/points",
    response_model=List[PointsAssignedToUser],
    summary=summary_get_points_of_user_in_game,
    description=description_get_points_of_user_in_game,
    responses=responses_get_points_of_user_in_game,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_of_user_in_game(
    gameId: UUID,
    externalUserId: str,
    service: UserPointsService = Depends(Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve points of a user in a specific game.

    Args:
        gameId (UUID): The ID of the game.
        externalUserId (str): The external user ID.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[PointsAssignedToUser]: The points details of the user in the
          specified game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "User points retrieval by game ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "User points retrieval by game ID",
        {"gameId": str(gameId), "externalUserId": externalUserId},
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_points_of_user_in_game(gameId, externalUserId)


summary_get_points_simulated_of_user_in_game = "Retrieve Simulated User Points in Game"
response_example_get_points_simulated_of_user_in_game = {
    "simulationHash": "8e9fc0f2ef79ed3fca6053a5932f7a6d8f3f3f77b2437d2b7d8ea59e21a4fd4e",
    "tasks": [
        {
            "externalUserId": "user-123",
            "externalTaskId": "task-login",
            "userGroup": "control",
            "dimensions": [
                {"name": "engagement", "value": 0.74},
                {"name": "consistency", "value": 0.61},
            ],
            "totalSimulatedPoints": 42,
            "expirationDate": "2026-02-11T00:00:00Z",
        },
        {
            "externalUserId": "user-123",
            "externalTaskId": "task-share",
            "userGroup": "control",
            "dimensions": [
                {"name": "engagement", "value": 0.55},
                {"name": "consistency", "value": 0.48},
            ],
            "totalSimulatedPoints": 18,
            "expirationDate": "2026-02-11T00:00:00Z",
        },
    ],
}

responses_get_points_simulated_of_user_in_game = {
    200: {
        "description": "Simulated points retrieved successfully",
        "content": {
            "application/json": {
                "example": response_example_get_points_simulated_of_user_in_game
            }
        },
    },
    401: {
        "description": "Unauthorized: missing/invalid/expired bearer token",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: token user is not allowed to access the requested external user id",
        "content": {
            "application/json": {
                "example": {
                    "detail": "You are not authorized to access this resource."
                }
            }
        },
    },
    404: {
        "description": "Game or user context not found for simulation",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find simulation context for gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521 and externalUserId = user-123"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
    },
    500: {
        "description": "Internal server error (for example: missing SECRET_KEY or simulation processing failure)",
    },
}

description_get_points_simulated_of_user_in_game = """
Returns simulated points for a user in a game, including per-task simulation breakdown.

### Path Parameters
- `gameId` (`UUID`, required): Internal game identifier.
- `externalUserId` (`string`, required): External user identifier to simulate.

### Authentication
- Requires OAuth2 bearer token (`Authorization: Bearer <access_token>`).
- API key authentication is not accepted on this endpoint.

### Access Control
- Caller can only access simulations allowed by token/user matching rules.
- Unauthorized cross-user access returns `403`.

### Success (200)
Returns:
- `simulationHash`: deterministic hash for simulation payload integrity
- `tasks`: list of simulated task point objects (`dimensions`, `userGroup`, `totalSimulatedPoints`, `expirationDate`)

### Error Cases
- `401`: missing/invalid/expired bearer token
- `403`: not authorized for requested `externalUserId`
- `404`: simulation context not found
- `422`: malformed path parameters
- `500`: missing environment configuration (`SECRET_KEY`) or simulation failure

<sub>**Id_endpoint:** `get_points_simulated_of_user_in_game`</sub>
"""  # noqa


@router.get(
    "/{gameId}/users/{externalUserId}/points/simulated",
    response_model=SimulatedPointsAssignedToUser,
    summary=summary_get_points_simulated_of_user_in_game,
    description=description_get_points_simulated_of_user_in_game,
    responses=responses_get_points_simulated_of_user_in_game,
    dependencies=[Depends(auth_oauth2)],
)
@inject
async def get_points_simulated_of_user_in_game(
    gameId: UUID,
    externalUserId: str,
    service: UserPointsService = Depends(Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_user: UserService = Depends(Provide[Container.user_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
):
    """
    Retrieve simulated points of a user in a specific game.

    Args:
        gameId (UUID): The ID of the game.
        externalUserId (str): The external user ID.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_user (UserService): Injected UserService dependency.

    Returns:
        List[SimulatedPointsAssignedToUser]: The simulated points details of the user in the specified game.
    """
    # user = await service_user.get_user_by_external_id(externalUserId)
    # if user is None:
    #     raise NotFoundError(
    #         detail=f"User with external ID {externalUserId} not found.")

    if not configs.SECRET_KEY:
        raise InternalServerError(
            detail="SECRET_KEY is not set. Please set the SECRET_KEY in the environment variables"
        )
    token_data = await valid_access_token(token)
    token_data = token_data.data
    oauth_user_id = token_data["sub"]
    is_admin = check_role(token_data, "AdministratorGAME")
    if is_admin and (not (oauth_user_id == externalUserId)):
        raise ForbiddenError(detail="You are not authorized to access this resource.")

    if service_oauth.get_user_by_sub(oauth_user_id) is None:
        create_user = CreateOAuthUser(
            provider="keycloak",
            provider_user_id=oauth_user_id,
            status="active",
        )
        service_oauth.add(create_user)
        await add_log(
            "game",
            "INFO",
            "Simulated user points retrieval by game ID - User created",
            {"oauth_user_id": oauth_user_id},
            service_log,
            None,
            oauth_user_id,
        )

    tasks_simulated, externalGameId = (
        await service.get_points_simulated_of_user_in_game(
            gameId,
            externalUserId,
            oauth_user_id=oauth_user_id,
            assign_control_group=True,
        )
    )

    simulationHash = calculate_hash_simulated_strategy(
        tasks_simulated,
        externalGameId,
        externalUserId,
    )

    response = SimulatedPointsAssignedToUser(
        simulationHash=simulationHash, tasks=tasks_simulated
    )

    await add_log(
        "game",
        "INFO",
        "Simulated user points retrieval by game ID",
        {
            "gameId": str(gameId),
            "externalUserId": externalUserId,
            "response": response.dict(),
        },
        service_log,
        None,
        oauth_user_id,
    )
    return response


summary_user_action = "User Action"
request_example_user_action = {
    "typeAction": "TASK_COMPLETED",
    "data": {
        "durationSeconds": 84,
        "source": "mobile-app",
        "metadata": {"difficulty": "easy"},
    },
    "description": "User completed the task from mobile flow",
    "externalUserId": "user-123",
}

response_example_user_action = {
    "id": "8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
    "created_at": "2026-02-10T12:40:00Z",
    "updated_at": "2026-02-10T12:40:00Z",
    "typeAction": "TASK_COMPLETED",
    "data": {
        "durationSeconds": 84,
        "source": "mobile-app",
        "metadata": {"difficulty": "easy"},
    },
    "description": "User completed the task from mobile flow",
    "externalUserId": "user-123",
    "message": "Successfully created",
}

responses_user_action = {
    200: {
        "description": "User action registered successfully",
        "content": {"application/json": {"example": response_example_user_action}},
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game, task, or user not found for the provided identifiers",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find task with externalTaskId = task-login for gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path/body payload",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "typeAction"],
                            "msg": "field required",
                            "type": "value_error.missing",
                        }
                    ]
                }
            }
        },
    },
    500: {
        "description": "Internal server error while registering user action",
        "content": {
            "application/json": {
                "example": {"detail": "Error when registering user action in task"}
            }
        },
    },
}

description_user_action = """
Registers an explicit user action event for a task inside a game.

### Path Parameters
- `gameId` (`UUID`, required): Internal game identifier.
- `externalTaskId` (`string`, required): External task identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Request Body
- `typeAction` (`string`, required): Business action/event type.
- `data` (`object`, required): Structured event payload used for audit and scoring logic.
- `description` (`string`, required): Human-readable action description.
- `externalUserId` (`string`, required): External user identifier that triggered the action.

### Success (200)
Returns the persisted action event:
- action metadata (`id`, timestamps)
- action payload (`typeAction`, `data`, `description`)
- actor (`externalUserId`)
- operation message (`message`)

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: game/task/user not found
- `422`: malformed path parameters or invalid request payload
- `500`: action registration failure

<sub>**Id_endpoint:** `user_action_in_task`</sub>
"""  # noqa


@router.post(
    "/{gameId}/tasks/{externalTaskId}/action",
    response_model=ResponseAddActionDidByUserInTask,
    summary=summary_user_action,
    description=description_user_action,
    responses=responses_user_action,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def user_action_in_task(
    gameId: UUID,
    externalTaskId: str,
    schema: AddActionDidByUserInTask = Body(..., example=request_example_user_action),
    service: UserActionsService = Depends(Provide[Container.user_actions_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Register a user action in a task within a game. This endpoint is used to
    assign points to a user for a specific task within a game, when the game
    requires it.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        schema (AddActionDidByUserInTask): The schema for adding an action.
        service (UserActionsService): Injected UserActionsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ResponseAddActionDidByUserInTask: The details of the action added.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "User action in task - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "User action in task",
        {
            "gameId": str(gameId),
            "externalTaskId": externalTaskId,
            "body": schema.dict(),
        },
        service_log,
        api_key,
        oauth_user_id,
    )

    return await service.user_add_action_in_task(
        gameId, externalTaskId, schema, api_key
    )


summary_assign_points_to_user = "Assign Points to User"
request_example_assign_points_to_user = {
    "externalUserId": "user-123",
    "data": {
        "event": "task_completed",
        "source": "mobile-app",
    },
    "isSimulated": False,
}

response_example_assign_points_to_user = {
    "points": 20,
    "caseName": "variable_basic_points",
    "isACreatedUser": True,
    "gameId": "4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    "externalTaskId": "task-login",
    "created_at": "2026-02-10T12:30:00Z",
}

responses_assign_points_to_user = {
    200: {
        "description": "Points assigned successfully",
        "content": {
            "application/json": {"example": response_example_assign_points_to_user}
        },
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game or task not found for provided identifiers",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find task with externalTaskId = task-login for gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path/body payload",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["path", "gameId"],
                            "msg": "value is not a valid uuid",
                            "type": "type_error.uuid",
                        }
                    ]
                }
            }
        },
    },
    500: {
        "description": "Internal server error while assigning points",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Error when assigning points to user in task"
                }
            }
        },
    },
}

description_assign_points_to_user = """
Assigns points to one user for a specific task in a game.

### Path Parameters
- `gameId` (`UUID`, required): Internal game identifier.
- `externalTaskId` (`string`, required): External task identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Request Body
- `externalUserId` (`string`, required): External user identifier that will receive points.
- `data` (`object`, optional): Task/event payload used by scoring strategy.
- `isSimulated` (`boolean`, optional): If `true`, executes simulation logic when supported.

### Success (200)
Returns the assigned points event:
- `points`
- `caseName`
- `isACreatedUser`
- `gameId`
- `externalTaskId`
- `created_at`

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: game/task association not found
- `422`: malformed path parameters or invalid request payload
- `500`: assignment failure

<sub>**Id_endpoint:** `assign_points_to_user`</sub>
"""  # noqa


@router.post(
    "/{gameId}/tasks/{externalTaskId}/points",
    response_model=AssignedPointsToExternalUserId,
    summary=summary_assign_points_to_user,
    description=description_assign_points_to_user,
    responses=responses_assign_points_to_user,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def assign_points_to_user(
    gameId: UUID,
    externalTaskId: str,
    schema: AsignPointsToExternalUserId = Body(
        ..., example=request_example_assign_points_to_user
    ),
    service: UserPointsService = Depends(Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Assign points to a user for a specific task in a game.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        schema (AsignPointsToExternalUserId): The schema for assigning points.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        AssignedPointsToExternalUserId: The details of the points assigned.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Points assignment to user - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Points assignment to user",
        {
            "gameId": str(gameId),
            "externalTaskId": externalTaskId,
            "body": schema.dict(),
        },
        service_log,
        api_key,
        oauth_user_id,
    )
    isSimulated = schema.isSimulated if hasattr(schema, "isSimulated") else False
    return await service.assign_points_to_user(
        gameId, externalTaskId, schema, isSimulated, api_key
    )


summary_get_points_by_task_id = "Retrieve Points by Task ID"
response_example_get_points_by_task_id = [
    {
        "externalUserId": "user-123",
        "points": 120,
        "timesAwarded": 6,
    },
    {
        "externalUserId": "user-456",
        "points": 40,
        "timesAwarded": 2,
    },
]

responses_get_points_by_task_id = {
    200: {
        "description": "Points by task retrieved successfully",
        "content": {"application/json": {"example": response_example_get_points_by_task_id}},
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game/task not found for provided identifiers",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find task with externalTaskId = task-login for gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
    },
    500: {
        "description": "Internal server error while retrieving task points",
    },
}

description_get_points_by_task_id = """
Returns point totals for all users in a specific task.

### Path Parameters
- `gameId` (`UUID`, required): Internal game identifier.
- `externalTaskId` (`string`, required): External task identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns a list of per-user aggregates:
- `externalUserId`
- `points`
- `timesAwarded`

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: game/task association not found
- `422`: malformed path parameters
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_points_by_task_id`</sub>
"""  # noqa


@router.get(
    "/{gameId}/tasks/{externalTaskId}/points",
    response_model=List[PointsAssignedToUser],
    summary=summary_get_points_by_task_id,
    description=description_get_points_by_task_id,
    responses=responses_get_points_by_task_id,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_by_task_id(
    gameId: UUID,
    externalTaskId: str,
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve points by task ID.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[PointsAssignedToUser]: The points details for the specified task.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Points retrieval by task ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Points retrieval by task ID",
        {"gameId": str(gameId), "externalTaskId": externalTaskId},
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_points_by_task_id(gameId, externalTaskId)


summary_get_points_of_user_by_task_id = "Retrieve User Points by Task ID"
response_example_get_points_of_user_by_task_id = {
    "externalUserId": "user-123",
    "points": 120,
    "timesAwarded": 6,
}

responses_get_points_of_user_by_task_id = {
    200: {
        "description": "User points by task retrieved successfully",
        "content": {
            "application/json": {
                "example": response_example_get_points_of_user_by_task_id
            }
        },
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game/task/user combination not found",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not find points for externalUserId = user-123 in externalTaskId = task-login for gameId = 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["path", "gameId"],
                            "msg": "value is not a valid uuid",
                            "type": "type_error.uuid",
                        }
                    ]
                }
            }
        },
    },
    500: {
        "description": "Internal server error while retrieving user task points",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Error when retrieving points for user in task"
                }
            }
        },
    },
}

description_get_points_of_user_by_task_id = """
Returns the aggregated points of one user in one task within a game.

### Path Parameters
- `gameId` (`UUID`, required): Internal game identifier.
- `externalTaskId` (`string`, required): External task identifier.
- `externalUserId` (`string`, required): External user identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns:
- `externalUserId`
- `points` (total points awarded in this task)
- `timesAwarded` (number of scoring events for this user-task pair)

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: no points record for the provided game/task/user combination
- `422`: malformed path parameters
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_points_of_user_by_task_id`</sub>
"""  # noqa


@router.get(
    "/{gameId}/tasks/{externalTaskId}/users/{externalUserId}/points",
    response_model=PointsAssignedToUser,
    summary=summary_get_points_of_user_by_task_id,
    description=description_get_points_of_user_by_task_id,
    responses=responses_get_points_of_user_by_task_id,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_of_user_by_task_id(
    gameId: UUID,
    externalTaskId: str,
    externalUserId: str,
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve points of a user by task ID.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        externalUserId (str): The external user ID.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        PointsAssignedToUser: The points details of the user for the specified
          task.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "User points retrieval by task ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "User points retrieval by task ID",
        {
            "gameId": str(gameId),
            "externalTaskId": externalTaskId,
            "externalUserId": externalUserId,
        },
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_points_of_user_by_task_id(gameId, externalTaskId, externalUserId)


summary_get_points_by_task_id_with_details = (
    "Retrieve Detailed Points by Task ID"  # noqa
)
response_example_get_points_by_task_id_with_details = [
    {
        "externalUserId": "user-123",
        "points": 120,
        "timesAwarded": 6,
        "pointsData": [
            {
                "points": 20,
                "caseName": "variable_basic_points",
                "data": {"event": "task_completed", "source": "mobile-app"},
                "description": "Awarded after completing task",
                "created_at": "2026-02-10T12:30:00Z",
            },
            {
                "points": 10,
                "caseName": "bonus_consistency",
                "data": {"streak": 3},
                "description": "Consistency bonus",
                "created_at": "2026-02-10T13:15:00Z",
            },
        ],
    },
    {
        "externalUserId": "user-456",
        "points": 40,
        "timesAwarded": 2,
        "pointsData": [
            {
                "points": 20,
                "caseName": "variable_basic_points",
                "data": {"event": "task_completed", "source": "web"},
                "description": "Awarded after completing task",
                "created_at": "2026-02-10T12:45:00Z",
            }
        ],
    },
]

responses_get_points_by_task_id_with_details = {
    200: {
        "description": "Detailed points by task retrieved successfully",
        "content": {
            "application/json": {
                "example": response_example_get_points_by_task_id_with_details
            }
        },
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game/task combination not found",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Task not found with externalTaskId: task-login for gameId: 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["path", "gameId"],
                            "msg": "value is not a valid uuid",
                            "type": "type_error.uuid",
                        }
                    ]
                }
            }
        },
    },
    500: {
        "description": "Internal server error while retrieving detailed task points",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Error when retrieving detailed points by task"
                }
            }
        },
    },
}

description_get_points_by_task_id_with_details = """
Returns detailed scoring history for all users in a task, including aggregated totals and per-award entries.

### Path Parameters
- `gameId` (`UUID`, required): Internal game identifier.
- `externalTaskId` (`string`, required): External task identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns a list where each item represents one user in the task:
- `externalUserId`
- `points` (total accumulated points in the task)
- `timesAwarded` (number of award events)
- `pointsData[]` (detailed award events with `points`, `caseName`, `data`, `description`, `created_at`)

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: task not found for the provided game/task identifiers
- `422`: malformed path parameters
- `500`: retrieval failure

<sub>**Id_endpoint:** get_points_by_task_id_with_details</sub>
"""  # noqa


@router.get(
    "/{gameId}/tasks/{externalTaskId}/points/details",
    response_model=List[dict],  # WIP FIX
    summary=summary_get_points_by_task_id_with_details,
    description=description_get_points_by_task_id_with_details,
    responses=responses_get_points_by_task_id_with_details,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_by_task_id_with_details(
    gameId: UUID,
    externalTaskId: str,
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve detailed points by task ID.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[dict]: Detailed points information for the specified task.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Detailed points retrieval by task ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Detailed points retrieval by task ID",
        {"gameId": str(gameId), "externalTaskId": externalTaskId},
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_points_by_task_id_with_details(gameId, externalTaskId)


summary_get_users_by_gameId = "Retrieve Users by Game ID"
response_example_get_users_by_gameId = {
    "gameId": "4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    "tasks": [
        {
            "externalTaskId": "task-login",
            "users": [
                {
                    "externalUserId": "user-123",
                    "created_at": "2026-02-10 12:20:00",
                    "firstAction": "2026-02-10 12:30:00",
                },
                {
                    "externalUserId": "user-456",
                    "created_at": "2026-02-10 12:25:00",
                    "firstAction": "2026-02-10 12:40:00",
                },
            ],
        },
        {
            "externalTaskId": "task-share",
            "users": [],
        },
    ],
}

responses_get_users_by_gameId = {
    200: {
        "description": "Users grouped by task retrieved successfully",
        "content": {
            "application/json": {"example": response_example_get_users_by_gameId}
        },
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    404: {
        "description": "Game or tasks not found for provided game identifier",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Tasks not found by gameId: 4ce32be2-77f6-4ffc-8e07-78dc220f0520"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["path", "gameId"],
                            "msg": "value is not a valid uuid",
                            "type": "type_error.uuid",
                        }
                    ]
                }
            }
        },
    },
    500: {
        "description": "Internal server error while retrieving users by game",
        "content": {
            "application/json": {
                "example": {"detail": "Error when retrieving users by gameId"}
            }
        },
    },
}

description_get_users_by_gameId = """
Returns users associated with each task in the specified game.

### Path Parameter
- `gameId` (`UUID`, required): Internal game identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns a task-grouped structure:
- `gameId`: requested game identifier
- `tasks`: list of tasks in the game
- `tasks[].externalTaskId`: external task identifier
- `tasks[].users`: users who have point activity in that task
- `tasks[].users[].externalUserId`: external user identifier
- `tasks[].users[].created_at`: user creation date
- `tasks[].users[].firstAction`: first points event timestamp for that task/user

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: game not found or game has no tasks
- `422`: malformed `gameId` (invalid UUID format)
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_users_by_gameId`</sub>
"""  # noqa


@router.get(
    "/{gameId}/users",
    response_model=ListTasksWithUsers,
    summary=summary_get_users_by_gameId,
    description=description_get_users_by_gameId,
    responses=responses_get_users_by_gameId,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_users_by_gameId(
    gameId: UUID,
    service: UserPointsService = Depends(Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve users associated with a game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ListTasksWithUsers: The list of users associated with the specified
          game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Users retrieval by game ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Users retrieval by game ID",
        {"gameId": str(gameId)},
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_users_by_gameId(gameId)
