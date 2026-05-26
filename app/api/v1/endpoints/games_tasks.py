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
    create_query: CreateTaskPost = Body(..., examples=[request_example_create_task]),
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
        {"gameId": str(gameId), "body": create_query.model_dump()},
        service_log,
        api_key,
        oauth_user_id,
    )
    try:
        response = await service.create_task_by_game_id(
            gameId,
            create_query,
            api_key,
            oauth_user_id=oauth_user_id,
            is_admin=is_admin,
            enforce_scope=True,
        )
        data_to_log = {"gameId": str(gameId), "body": create_query.model_dump()}
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
    create_query: CreateTasksPost = Body(..., examples=[request_example_create_tasks_bulk]),
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
        {"gameId": str(gameId), "body": create_query.model_dump()},
        service_log,
        api_key,
        oauth_user_id,
    )

    for task in create_query.tasks:
        try:
            created_task = await service.create_task_by_game_id(
                gameId,
                task,
                api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
                enforce_scope=True,
            )
            succesfully_created.append(created_task)
        except ForbiddenError:
            raise
        except Exception as e:
            failed_to_create.append({"task": task, "error": str(e)})
    if len(failed_to_create) > 0:
        await add_log(
            "game",
            "ERROR",
            "Bulk task creation failed",
            {
                "gameId": str(gameId),
                "body": create_query.model_dump(),
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
                "body": create_query.model_dump(),
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
        {"gameId": str(gameId), "body": find_query.model_dump()},
        service_log,
        api_key,
        oauth_user_id,
    )
    return await service.get_tasks_list_by_gameId(
        gameId,
        find_query,
        **_game_access_kwargs(api_key, oauth_user_id, is_admin),
    )


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

    return await service.get_task_by_externalGameId_externalTaskId(
        str(gameId),
        externalTaskId,
        **_game_access_kwargs(api_key, oauth_user_id, is_admin),
    )


