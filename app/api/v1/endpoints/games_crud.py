import logging
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends

from app.api.v1.endpoints.games_common import _game_access_kwargs
from app.core.container import Container
from app.middlewares.auth_context import AuditLogger, audit_log
from app.middlewares.authentication import auth_api_key_or_oauth2
from app.schema.games_schema import (BaseGameResult, DuplicateGame, FindGameResult,
                                     GameCreated, PatchGame, PostCreateGame,
                                     PostFindGame, ResponsePatchGame)
from app.services.game_service import GameService

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
    audit: AuditLogger = Depends(audit_log("game")),
):
    """
    Retrieve a list of all games with their parameters.

    Args:
        schema(PostFindGame): Query parameters for finding games.
        service(GameService): Injected GameService dependency.
        audit(AuditLogger): Per-request audit logger bound to the auth context.


    Returns:
        FindGameResult: A result set containing the games and search options.
    """
    auth = audit.auth
    await audit.info("Game list retrieval", schema.model_dump())
    return await service.get_all_games(
        schema,
        api_key=auth.api_key,
        oauth_user_id=auth.oauth_user_id,
        is_admin=auth.is_admin,
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
    audit: AuditLogger = Depends(audit_log("game")),
):
    """
    Retrieve a game by its ID.

    Args:
        gameId(UUID): The ID of the game.
        service(GameService): Injected GameService dependency.
        audit(AuditLogger): Per-request audit logger bound to the auth context.

    Returns:
        BaseGameResult: The details of the specified game.
    """
    auth = audit.auth
    await audit.info("Game retrieval by ID", {"gameId": str(gameId)})
    return await service.get_by_gameId(
        gameId,
        **_game_access_kwargs(auth.api_key, auth.oauth_user_id, auth.is_admin),
    )


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
        "content": {
            "application/json": {"example": response_example_delete_game_by_id}
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
    audit: AuditLogger = Depends(audit_log("game")),
):
    """
    Delete a game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (GameService): Injected GameService dependency.
        audit (AuditLogger): Per-request audit logger bound to the auth context.

    Returns:
        BaseGameResult: The details of the deleted game.
    """
    auth = audit.auth
    await audit.info("Game deletion by ID", {"gameId": str(gameId)})

    try:
        response = await service.delete_game_by_id(
            gameId,
            **_game_access_kwargs(auth.api_key, auth.oauth_user_id, auth.is_admin),
        )
        await audit.success("Game deletion successful", {"gameId": str(gameId)})
        return response
    except Exception as e:
        await audit.error("Game deletion failed", {"error": str(e)})
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
    audit: AuditLogger = Depends(audit_log("game")),
):
    """
    Create a new game.

    Args:
        schema (PostCreateGame): The schema for creating a new game.
        service (GameService): Injected GameService dependency.
        audit (AuditLogger): Per-request audit logger bound to the auth context.

    Returns:
        GameCreated: The details of the created game.
    """

    auth = audit.auth
    await audit.info("Game creation", schema.model_dump())
    try:
        response = await service.create(schema, auth.api_key, auth.oauth_user_id)
        data_to_log = {"body": schema.model_dump(), "gameId": str(response.gameId)}
        await audit.success("Game creation successful", data_to_log)
        return response
    except Exception as e:
        await audit.error("Game creation failed", {"error": str(e)})
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
    audit: AuditLogger = Depends(audit_log("game")),
):
    """
    Update a game by its ID.

    Args:
        gameId (UUID): The ID of the game to update.
        schema (PatchGame): The schema for updating the game.
        service (GameService): Injected GameService dependency.
        audit (AuditLogger): Per-request audit logger bound to the auth context.

    Returns:
        ResponsePatchGame: The updated game details.
    """
    auth = audit.auth
    await audit.info(
        "Game update by ID", {"gameId": str(gameId), "body": schema.model_dump()}
    )

    try:
        response = await service.patch_game_by_id(
            gameId,
            schema,
            **_game_access_kwargs(auth.api_key, auth.oauth_user_id, auth.is_admin),
        )
        data_to_log = {"gameId": str(gameId), "body": schema.model_dump()}
        await audit.success("Game update successful", data_to_log)
        return response
    except Exception as e:
        await audit.error("Game update failed", {"error": str(e)})
        raise e


summary_duplicate_game = "Duplicate a Game (deep copy)"
request_example_duplicate_game = {"externalGameId": "copy-of-game-readme-001"}
responses_duplicate_game = {
    200: {
        "description": "Game duplicated successfully",
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
    404: {
        "description": "Source game not found for the provided id",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Game not found by gameId: 4ce32be2-77f6-4ffc-8e07-78dc220f0521"
                }
            }
        },
    },
    409: {
        "description": "A game with the new externalGameId already exists",
    },
    422: {
        "description": "Validation error in path/body payload",
    },
    500: {
        "description": "Internal server error while duplicating game",
    },
}

description_duplicate_game = """
Deep-copies a game into a brand new one under the provided `externalGameId`.

### Path Parameter
- `gameId` (`UUID`, required): Internal identifier of the game to copy.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Request Body
- `externalGameId` (`string`, required): External identifier for the new
  game. Must be unique.

### Behaviour
Copies the source game's platform, strategy and params, then every task
with its own strategy and params. The standard game-creation guards (slug
validation, externalGameId uniqueness, strategy existence) run against the
copy. Duplicated tasks start in the default `open` status.

### Success (200)
Returns the created game metadata and persisted parameters, same shape as
`create_game`.

### Error Cases
- `401`/`403`: missing/invalid auth or scope.
- `404`: source game not found.
- `409`: a game with the new `externalGameId` already exists.
- `422`: malformed UUID or invalid request payload.
- `500`: duplication failure.

<sub>**Id_endpoint:** `duplicate_game`</sub>
"""  # noqa


@router.post(
    "/{gameId}/duplicate",
    response_model=GameCreated,
    summary=summary_duplicate_game,
    description=description_duplicate_game,
    responses=responses_duplicate_game,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def duplicate_game(
    gameId: UUID,
    schema: DuplicateGame = Body(..., examples=[request_example_duplicate_game]),
    service: GameService = Depends(Provide[Container.game_service]),
    audit: AuditLogger = Depends(audit_log("game")),
):
    """
    Duplicate a game (deep copy) under a new externalGameId.

    Sprint 0 (CRUD): backs the dashboard's "Duplicate" action so an admin
    can clone an existing game - with all its tasks and params - as the
    starting point for a new one.
    """
    auth = audit.auth
    await audit.info(
        "Game duplication",
        {"gameId": str(gameId), "body": schema.model_dump()},
    )
    try:
        response = await service.duplicate_game(
            gameId,
            schema.externalGameId,
            **_game_access_kwargs(auth.api_key, auth.oauth_user_id, auth.is_admin),
        )
        await audit.success(
            "Game duplication successful",
            {
                "gameId": str(gameId),
                "newGameId": str(response.gameId),
                "body": schema.model_dump(),
            },
        )
        return response
    except Exception as e:
        await audit.error("Game duplication failed", {"error": str(e)})
        raise e
