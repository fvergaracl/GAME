import logging
import traceback
from typing import List, Optional
from uuid import UUID, uuid4

import jwt
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError

from app.api.v1.endpoints.games_common import (
    _extract_api_key_from_header,
    _extract_db_error_code,
    _extract_oauth_user_id_from_token,
    _game_access_kwargs,
    _map_write_exception,
    _resolve_correlation_id,
    _resolve_idempotency_key,
)
from app.core.config import configs
from app.core.container import Container
from app.core.exceptions import (ConflictError, DuplicatedError, ForbiddenError,
                                 InternalServerError, NotFoundError,
                                 PreconditionFailedError)
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
from app.services.abuse_prevention_service import AbusePreventionService
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

logger = logging.getLogger(__name__)


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
    api_key = _extract_api_key_from_header(api_key_header)
    oauth_user_id = None
    is_admin = False
    if token:
        token_data = await valid_access_token(token)
        token_data = token_data.data
        oauth_user_id = token_data["sub"]
        if await service_oauth.get_user_by_sub(oauth_user_id) is None:
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
    await add_log(
        "game",
        "INFO",
        "Game list retrieval",
        schema.model_dump(),
        service_log,
        api_key,
        oauth_user_id,
    )
    return await service.get_all_games(
        schema,
        api_key=api_key,
        oauth_user_id=oauth_user_id,
        is_admin=is_admin,
    )


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
    api_key = _extract_api_key_from_header(api_key_header)
    oauth_user_id = None
    is_admin = False
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        is_admin = check_role(token_data.data, "AdministratorGAME")
        if await service_oauth.get_user_by_sub(oauth_user_id) is None:
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
    response = await service.get_by_gameId(
        gameId, **_game_access_kwargs(api_key, oauth_user_id, is_admin)
    )
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
    api_key = _extract_api_key_from_header(api_key_header)
    oauth_user_id = None
    is_admin = False
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        is_admin = check_role(token_data.data, "AdministratorGAME")
        if await service_oauth.get_user_by_sub(oauth_user_id) is None:
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
        response = await service.delete_game_by_id(
            gameId, **_game_access_kwargs(api_key, oauth_user_id, is_admin)
        )
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
    schema: PostCreateGame = Body(..., examples=[request_example_create_game]),
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

    api_key = _extract_api_key_from_header(api_key_header)
    oauth_user_id = None
    is_admin = False
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        is_admin = check_role(token_data.data, "AdministratorGAME")
        if await service_oauth.get_user_by_sub(oauth_user_id) is None:
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
        schema.model_dump(),
        service_log,
        api_key,
        oauth_user_id,
    )
    try:
        response = await service.create(schema, api_key, oauth_user_id)
        data_to_log = {"body": schema.model_dump(), "gameId": str(response.gameId)}
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
    schema: PatchGame = Body(..., examples=[request_example_patch_game]),
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
    api_key = _extract_api_key_from_header(api_key_header)
    oauth_user_id = None
    is_admin = False
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        is_admin = check_role(token_data.data, "AdministratorGAME")
        if await service_oauth.get_user_by_sub(oauth_user_id) is None:
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
        {"gameId": str(gameId), "body": schema.model_dump()},
        service_log,
        api_key,
        oauth_user_id,
    )

    try:
        response = await service.patch_game_by_id(
            gameId,
            schema,
            **_game_access_kwargs(api_key, oauth_user_id, is_admin),
        )
        data_to_log = {"gameId": str(gameId), "body": schema.model_dump()}
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


