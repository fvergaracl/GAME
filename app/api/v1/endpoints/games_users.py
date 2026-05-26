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
    return await service.get_users_by_gameId(
        gameId, **_game_access_kwargs(api_key, oauth_user_id, is_admin)
    )
