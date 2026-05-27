import logging
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.api.v1.endpoints.games_common import _game_access_kwargs
from app.core.container import Container
from app.middlewares.auth_context import AuditLogger, audit_log
from app.middlewares.authentication import auth_api_key_or_oauth2
from app.schema.strategy_schema import Strategy
from app.services.game_service import GameService

router = APIRouter(
    prefix="/games",
    tags=["games"],
)

logger = logging.getLogger(__name__)


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
    audit: AuditLogger = Depends(audit_log("game")),
):
    """
    Retrieve the strategy associated with a game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (GameService): Injected GameService dependency.
        audit (AuditLogger): Per-request audit logger bound to the auth context.

    Returns:
        Strategy: The strategy associated with the specified game.
    """
    auth = audit.auth
    await audit.info("Strategy retrieval by game ID", {"gameId": str(gameId)})

    return await service.get_strategy_by_gameId(
        gameId, **_game_access_kwargs(auth.api_key, auth.oauth_user_id, auth.is_admin)
    )
