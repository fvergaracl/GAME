import logging
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.api.v1.endpoints.games_common import _game_access_kwargs
from app.core.container import Container
from app.middlewares.auth_context import AuditLogger, audit_log
from app.middlewares.authentication import auth_api_key_or_oauth2
from app.schema.games_schema import ListTasksWithUsers
from app.services.user_points_service import UserPointsService

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
    audit: AuditLogger = Depends(audit_log("game")),
):
    """
    Retrieve users associated with a game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (UserPointsService): Injected UserPointsService dependency.
        audit (AuditLogger): Per-request audit logger bound to the auth context.

    Returns:
        ListTasksWithUsers: The list of users associated with the specified
          game.
    """
    auth = audit.auth
    await audit.info("Users retrieval by game ID", {"gameId": str(gameId)})
    return await service.get_users_by_gameId(
        gameId, **_game_access_kwargs(auth.api_key, auth.oauth_user_id, auth.is_admin)
    )
