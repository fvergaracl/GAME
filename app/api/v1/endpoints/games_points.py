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

    return await service.get_points_by_gameId(
        gameId, **_game_access_kwargs(api_key, oauth_user_id, is_admin)
    )


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

    return await service.get_points_by_gameId_with_details(
        gameId, **_game_access_kwargs(api_key, oauth_user_id, is_admin)
    )


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
    return await service.get_points_of_user_in_game(
        gameId,
        externalUserId,
        **_game_access_kwargs(api_key, oauth_user_id, is_admin),
    )


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
            is_admin=is_admin,
            enforce_scope=True,
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
            "response": response.model_dump(),
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
    429: {
        "description": "Too many requests: rate limit exceeded",
        "content": {
            "application/json": {
                "example": {
                    "detail": "API key rate limit exceeded for sensitive task operations."
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
    request: Request,
    schema: AddActionDidByUserInTask = Body(..., examples=[request_example_user_action]),
    service: UserActionsService = Depends(Provide[Container.user_actions_service]),
    abuse_prevention_service: AbusePreventionService = Depends(
        Provide[Container.abuse_prevention_service]
    ),
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
    api_key = _extract_api_key_from_header(api_key_header)
    oauth_user_id = _extract_oauth_user_id_from_token(token)
    is_admin = False
    if token and not api_key:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        is_admin = check_role(token_data.data, "AdministratorGAME")
    correlation_id = _resolve_correlation_id(request)
    if isinstance(schema.data, dict):
        schema.data.setdefault("correlationId", correlation_id)
        schema.data.setdefault("eventId", correlation_id)
    client_ip = abuse_prevention_service.extract_client_ip(request)
    await abuse_prevention_service.enforce_task_mutation_limits(
        api_key=api_key,
        client_ip=client_ip,
        external_user_id=schema.externalUserId,
    )
    await add_log(
        "game",
        "INFO",
        "User action in task",
        {
            "gameId": str(gameId),
            "externalTaskId": externalTaskId,
            "correlationId": correlation_id,
            "body": schema.model_dump(),
        },
        service_log,
        api_key,
        oauth_user_id,
    )
    try:
        return await service.user_add_action_in_task(
            gameId,
            externalTaskId,
            schema,
            api_key,
            oauth_user_id=oauth_user_id,
            is_admin=is_admin,
            enforce_scope=True,
        )
    except Exception as exc:
        mapped_exc = _map_write_exception(exc, correlation_id=correlation_id)
        error_payload = {
            "gameId": str(gameId),
            "externalTaskId": externalTaskId,
            "externalUserId": schema.externalUserId,
            "correlationId": correlation_id,
            "errorType": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        logger.exception(
            "user_action_in_task failed",
            extra=error_payload,
        )
        await add_log(
            "game",
            "ERROR",
            "User action in task failed",
            error_payload,
            service_log,
            api_key,
            oauth_user_id,
        )
        raise mapped_exc


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
    429: {
        "description": "Too many requests: rate limit exceeded",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Daily API key quota exceeded for sensitive task operations."
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
    request: Request,
    schema: AsignPointsToExternalUserId = Body(
        ..., examples=[request_example_assign_points_to_user]
    ),
    service: UserPointsService = Depends(Provide[Container.user_points_service]),
    abuse_prevention_service: AbusePreventionService = Depends(
        Provide[Container.abuse_prevention_service]
    ),
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
    api_key = _extract_api_key_from_header(api_key_header)
    oauth_user_id = _extract_oauth_user_id_from_token(token)
    is_admin = False
    if token and not api_key:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        is_admin = check_role(token_data.data, "AdministratorGAME")
    correlation_id = _resolve_correlation_id(request)
    idempotency_key = _resolve_idempotency_key(request)
    if schema.data is None:
        schema.data = {}
    if isinstance(schema.data, dict):
        schema.data.setdefault("correlationId", correlation_id)
        if idempotency_key:
            schema.data.setdefault("eventId", idempotency_key)
    client_ip = abuse_prevention_service.extract_client_ip(request)
    await abuse_prevention_service.enforce_task_mutation_limits(
        api_key=api_key,
        client_ip=client_ip,
        external_user_id=schema.externalUserId,
    )
    await add_log(
        "game",
        "INFO",
        "Points assignment to user",
        {
            "gameId": str(gameId),
            "externalTaskId": externalTaskId,
            "correlationId": correlation_id,
            "idempotencyKey": idempotency_key,
            "body": schema.model_dump(),
        },
        service_log,
        api_key,
        oauth_user_id,
    )
    isSimulated = schema.isSimulated if hasattr(schema, "isSimulated") else False
    try:
        return await service.assign_points_to_user(
            gameId,
            externalTaskId,
            schema,
            isSimulated,
            api_key,
            oauth_user_id=oauth_user_id,
            is_admin=is_admin,
            enforce_scope=True,
        )
    except Exception as exc:
        mapped_exc = _map_write_exception(exc, correlation_id=correlation_id)
        error_payload = {
            "gameId": str(gameId),
            "externalTaskId": externalTaskId,
            "externalUserId": schema.externalUserId,
            "correlationId": correlation_id,
            "idempotencyKey": idempotency_key,
            "errorType": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        logger.exception(
            "assign_points_to_user failed",
            extra=error_payload,
        )
        await add_log(
            "game",
            "ERROR",
            "Points assignment to user failed",
            error_payload,
            service_log,
            api_key,
            oauth_user_id,
        )
        raise mapped_exc


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
    return await service.get_points_by_task_id(
        gameId,
        externalTaskId,
        **_game_access_kwargs(api_key, oauth_user_id, is_admin),
    )


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
    return await service.get_points_of_user_by_task_id(
        gameId,
        externalTaskId,
        externalUserId,
        **_game_access_kwargs(api_key, oauth_user_id, is_admin),
    )


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
    return await service.get_points_by_task_id_with_details(
        gameId,
        externalTaskId,
        **_game_access_kwargs(api_key, oauth_user_id, is_admin),
    )


