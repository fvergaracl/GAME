from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Query

from app.core.container import Container
from app.middlewares.authentication import auth_api_key_or_oauth2
from app.middlewares.valid_access_token import oauth_2_scheme, valid_access_token
from app.schema.oauth_users_schema import CreateOAuthUser
from app.schema.user_actions_schema import CreatedUserActions, CreateUserBodyActions
from app.schema.user_points_schema import (AllPointsByGame, BaseUserPointsBaseModel,
                                           UserGamePoints, UserPointsAssigned)
from app.schema.user_schema import (PostAssignPointsToUserWithCaseName,
                                    PostPointsConversionRequest,
                                    ResponseConversionPreview, ResponsePointsConversion,
                                    UserWallet)
from app.services.apikey_service import ApiKeyService
from app.services.logs_service import LogsService
from app.services.oauth_users_service import OAuthUsersService
from app.services.user_actions_service import UserActionsService
from app.services.user_points_service import UserPointsService
from app.services.user_service import UserService
from app.util.add_log import add_log

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

"""
/users/points/query:
  post:
    tags:
      - users
    summary: Query User Points
    description: |
      ## Query User Points
      This endpoint retrieves the point totals for a list of users based on
        their external user IDs. This operation does not modify any user data.
    operationId: query_user_points
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              externalUserIds:
                type: array
                items:
                  type: string
            example:
              externalUserIds: ["user1", "user2", "user3"]
    responses:
      200:
        description: Successful response with point details for each user.
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  externalUserId:
                    type: string
                  points:
                    type: integer
              example:
                - externalUserId: "user1"
                  points: 120
                - externalUserId: "user2"
                  points: 150
                - externalUserId: "user3"
                  points: 90
      400:
        description: Bad request if the request body is not properly formatted.

"""

summary_query_user_points = "Query User Points by External IDs"
request_example_query_user_points = [
    "user-123",
    "user-456",
    "user-not-found",
]

response_example_query_user_points = [
    {
        "externalUserId": "user-123",
        "points": 160,
        "timesAwarded": 8,
        "games": [
            {
                "externalGameId": "game-readme-001",
                "points": 120,
                "timesAwarded": 6,
                "tasks": [
                    {
                        "externalTaskId": "task-login",
                        "pointsData": [
                            {
                                "points": 20,
                                "caseName": "variable_basic_points",
                                "created_at": "2026-02-10T12:30:00Z",
                            }
                        ],
                    }
                ],
            }
        ],
        "userExists": True,
    },
    {
        "externalUserId": "user-not-found",
        "points": 0,
        "timesAwarded": 0,
        "games": [],
        "userExists": False,
    },
]

responses_query_user_points = {
    200: {
        "description": "User points queried successfully",
        "content": {
            "application/json": {"example": response_example_query_user_points}
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
    422: {
        "description": "Validation error in request payload",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", 0],
                            "msg": "str type expected",
                            "type": "type_error.str",
                        }
                    ]
                }
            }
        },
    },
    500: {
        "description": "Internal server error while querying user points",
        "content": {
            "application/json": {
                "example": {"detail": "Error when querying user points"}
            }
        },
    },
}

description_query_user_points = """
Returns aggregated points for multiple users in one request, grouped by game and task.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Request Body
- Array of `externalUserId` values (`string[]`).
- The endpoint is read-only and does not modify user/game/task data.

### Success (200)
Returns one `UserGamePoints` item per requested external user id:
- `externalUserId`
- `points` and `timesAwarded` (global totals for that user)
- `games[]` with per-game totals and `tasks[]` details
- `userExists` indicating whether that external user exists in the system

### Behavior for Unknown Users
- Unknown `externalUserId` values are returned with `userExists=false`, `points=0`, `timesAwarded=0`, and empty `games`.

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `422`: invalid request payload (for example non-string items)
- `500`: query failure

<sub>**Id_endpoint:** `query_user_points`</sub>
"""  # noqa


@router.post(
    "/points/query",
    response_model=List[UserGamePoints],
    summary=summary_query_user_points,
    description=description_query_user_points,
    responses=responses_query_user_points,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def query_user_points(
    schema: List[str] = Body(..., example=request_example_query_user_points),
    service: UserPointsService = Depends(Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve point totals for a list of users based on their external user IDs.

    Args:
        schema (List[str]): A list of external user IDs.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): The OAuth users service.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[UserGamePoints]: The point details for each user.
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
                "users",
                "INFO",
                "Query user points - User created",
                {
                    "oauth_user_id": oauth_user_id,
                },
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
    try:
        await add_log(
            "users",
            "INFO",
            "Query user points",
            {"externalUserIds": schema},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        response = service.get_points_by_user_list(schema)
        return response
    except Exception as e:
        await add_log(
            "users",
            "ERROR",
            "Query user points failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise e


summary_get_user_points = "Retrieve User Points"
response_example_get_user_points = [
    {
        "externalGameId": "game-readme-001",
        "created_at": "2026-02-10 12:15:00",
        "task": [
            {
                "externalTaskId": "task-login",
                "points": [
                    {
                        "externalUserId": "user-123",
                        "points": 120,
                        "timesAwarded": 6,
                    }
                ],
            },
            {
                "externalTaskId": "task-share",
                "points": [
                    {
                        "externalUserId": "user-123",
                        "points": 40,
                        "timesAwarded": 2,
                    }
                ],
            },
        ],
    }
]

responses_get_user_points = {
    200: {
        "description": "User points retrieved successfully",
        "content": {
            "application/json": {"example": response_example_get_user_points}
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
        "description": "User not found for provided external identifier",
        "content": {
            "application/json": {
                "example": {
                    "detail": "User not found by externalUserId: user-123"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
    },
    500: {
        "description": "Internal server error while retrieving user points",
    },
}

description_get_user_points = """
Returns all points earned by a user grouped by game and task.

### Path Parameter
- `externalUserId` (`string`, required): External user identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns a list of games where the user has point records:
- `externalGameId`
- `created_at`
- `task[]`
- `task[].externalTaskId`
- `task[].points[]` with `externalUserId`, `points`, and `timesAwarded`

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: user not found
- `422`: invalid path parameters
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_user_points`</sub>
"""  # noqa


@router.get(
    "/{externalUserId}/points",
    response_model=List[AllPointsByGame],
    summary=summary_get_user_points,
    description=description_get_user_points,
    responses=responses_get_user_points,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_by_user_id(
    externalUserId: str,
    service: UserPointsService = Depends(Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve points associated with a user by their external user ID.

    Args:
        externalUserId (str): The external user ID.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): The OAuth users service.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[AllPointsByGame]: The points details for the specified user.
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
                "users",
                "INFO",
                "Get user points - User created",
                {
                    "oauth_user_id": oauth_user_id,
                },
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
    try:
        await add_log(
            "users",
            "INFO",
            "Get user points",
            {"externalUserId": externalUserId},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        response = service.get_points_by_externalUserId(externalUserId)
        return response
    except Exception as e:
        await add_log(
            "users",
            "ERROR",
            "Get user points failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise e


summary_get_user_wallet = "Retrieve User Wallet"
response_example_get_user_wallet = {
    "userId": "8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
    "wallet": {
        "coinsBalance": 12.5,
        "pointsBalance": 340.0,
        "conversionRate": 100.0,
    },
    "walletTransactions": [
        {
            "id": "51d2618d-43ab-4a3c-83ec-70f2f26f7f31",
            "created_at": "2026-02-10 14:20:00",
            "transactionType": "AssignPoints",
            "points": 20,
            "coins": 0.0,
            "data": {"externalTaskId": "task-login", "caseName": "variable_basic_points"},
        },
        {
            "id": "2a18d9a9-8eb5-4d33-a7bd-9590ea7ea41e",
            "created_at": "2026-02-10 15:05:00",
            "transactionType": "ConvertPointsToCoins",
            "points": 100,
            "coins": 1.0,
            "data": {"reason": "user_requested_conversion"},
        },
    ],
}

responses_get_user_wallet = {
    200: {
        "description": "User wallet retrieved successfully",
        "content": {
            "application/json": {"example": response_example_get_user_wallet}
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
        "description": "User not found for provided external identifier",
        "content": {
            "application/json": {
                "example": {
                    "detail": "User not found by externalUserId: user-123"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path parameters",
    },
    500: {
        "description": "Internal server error while retrieving user wallet",
    },
}

description_get_user_wallet = """
Returns wallet balances and wallet transaction history for a user identified by `externalUserId`.

### Path Parameter
- `externalUserId` (`string`, required): External user identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns:
- `userId`: internal user identifier
- `wallet`: current wallet balances (`coinsBalance`, `pointsBalance`, `conversionRate`)
- `walletTransactions[]`: transaction history (`transactionType`, `points`, `coins`, `data`, `created_at`)

### Notes
- If the user exists but has no wallet yet, a wallet is created automatically with default balances.

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: user not found
- `422`: invalid path parameters
- `500`: retrieval failure

<sub>**Id_endpoint:** `get_user_wallet`</sub>"""  # noqa


@router.get(
    "/{externalUserId}/wallet",
    response_model=UserWallet,
    summary=summary_get_user_wallet,
    description=description_get_user_wallet,
    responses=responses_get_user_wallet,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_wallet_by_user_id(
    externalUserId: str,
    service: UserService = Depends(Provide[Container.user_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve the wallet details associated with a user by their external user
      ID.

    Args:
        externalUserId (str): The external user ID.
        service (UserService): Injected UserService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): The OAuth users service.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        UserWallet: The wallet details for the specified user.
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
                "users",
                "INFO",
                "Get user wallet - User created",
                {
                    "oauth_user_id": oauth_user_id,
                },
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
    try:
        await add_log(
            "users",
            "INFO",
            "Get user wallet",
            {"externalUserId": externalUserId},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        response = await service.get_wallet_by_externalUserId(externalUserId)
        return response
    except Exception as e:
        await add_log(
            "users",
            "ERROR",
            "Get user wallet failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise e


# @router.get("")
# @inject
# def list_users(
#     schema: FindBase = Depends(),
#     service: UserService = Depends(Provide[Container.user_service]),
# ):
#     return service.get_list(schema)


# @router.post("", response_model=CreatedUser)
# @inject
# def create_user(
#     schema: PostCreateUser,
#     service: UserService = Depends(Provide[Container.user_service]),
# ):
#     return service.create_user(schema)


summary_assign_points_by_external_id = "Assign points to user by externalUserId"
response_example_assign_points_by_external_user_id = {
    "id": "4ef6fc17-1bc8-44a9-b3fa-8f8cc43cb9a2",
    "created_at": "2026-02-10T16:22:10Z",
    "updated_at": "2026-02-10T16:22:10Z",
    "userId": "8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
    "taskId": "2a18d9a9-8eb5-4d33-a7bd-9590ea7ea41e",
    "caseName": "field_entry",
    "points": 80,
    "description": "Reward for quick data input",
    "data": {
        "source": "mobile",
        "note": "Completed under 2 minutes",
        "label_function_choose": "-",
    },
    "wallet": {
        "coinsBalance": 12.5,
        "pointsBalance": 420.0,
        "conversionRate": 100.0,
    },
    "message": "Successfully assigned",
}

responses_assign_points_by_external_user_id = {
    200: {
        "description": "Points assigned successfully",
        "content": {
            "application/json": {
                "example": response_example_assign_points_by_external_user_id
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
        "description": "User or task not found for provided identifiers",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Task not found with externalTaskId: task-xyz"
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
                            "loc": ["body", "caseName"],
                            "msg": "field required",
                            "type": "value_error.missing",
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
                    "detail": "Error when assigning points by externalUserId"
                }
            }
        },
    },
}

description_assign_points_by_external_id = """
Assigns points to a user using the external user identifier instead of the internal UUID.

### Path Parameter
- `externalUserId` (`string`, required): External user identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Request Body
- `taskId` (`string`, required): External task identifier.
- `caseName` (`string`, required): Scoring case label used for audit/analytics.
- `points` (`integer`, optional): Explicit points to assign. If omitted, strategy logic may calculate points automatically.
- `description` (`string`, optional): Human-readable reason for the assignment.
- `data` (`object`, optional): Additional structured metadata persisted with the event.

### Success (200)
Returns the created points record and updated wallet state:
- assignment metadata (`id`, timestamps)
- assignment payload (`userId`, `taskId`, `caseName`, `points`, `description`, `data`)
- `wallet` snapshot after assignment
- operation `message`

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: user or task not found
- `422`: malformed path parameters or invalid request body
- `500`: assignment failure

<sub>**Id_endpoint:** `assign_points_by_externalUserId`</sub>
"""


example_payload_assign_points_by_external_user_id = {
    "taskId": "task-xyz",
    "caseName": "field_entry",
    "points": 80,
    "description": "Reward for quick data input",
    "data": {"source": "mobile", "note": "Completed under 2 minutes"},
}


@router.post(
    "/external/{externalUserId}/points",
    response_model=UserPointsAssigned,
    summary=summary_assign_points_by_external_id,
    description=description_assign_points_by_external_id,
    responses=responses_assign_points_by_external_user_id,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def assign_points_by_external_user_id(
    externalUserId: str,
    schema: PostAssignPointsToUserWithCaseName = Body(
        ...,
        example=example_payload_assign_points_by_external_user_id,
        description="Details of point assignment",
    ),
    service: UserService = Depends(Provide[Container.user_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Assign points to user based on externalUserId.

    Args:
        externalUserId (str): The external user ID.
        schema (PostAssignPointsToUser): The point assignment payload.
        service (UserService): User service to handle logic.
        token (str): OAuth token.
        api_key_header (str): API Key (optional).

    Returns:
        UserPointsAssigned: Information about the point assignment and wallet.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None

    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            await service_oauth.add(
                CreateOAuthUser(
                    provider="keycloak",
                    provider_user_id=oauth_user_id,
                    status="active",
                )
            )

    try:
        await add_log(
            "users",
            "INFO",
            "Assign points by externalUserId",
            {"externalUserId": externalUserId, "schema": schema.dict()},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )

        taskId = service.task_repository.read_by_column(
            "externalTaskId",
            schema.taskId,
            not_found_message=f"Task not found with externalTaskId: {schema.taskId}",
        )

        user = service.user_repository.read_by_column(
            "externalUserId",
            externalUserId,
            not_found_message=f"User not found with externalUserId: {externalUserId}",
        )

        schema_with_user_id = BaseUserPointsBaseModel(
            userId=str(user.id),
            taskId=str(taskId.id),
            points=schema.points,
            caseName=schema.caseName,
            description=schema.description,
            data=schema.data or {},
        )

        return await service.assign_points_to_user(
            user.id, schema_with_user_id, api_key
        )

    except Exception as e:
        await add_log(
            "users",
            "ERROR",
            "Assign points by externalUserId failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise e


summary_get_points = "Get points by user id"
description_get_points = """
## Get points by user id
### Get points by user id
"""


# @router.get(
#     "/{userId}/points",
#     response_model=UserPointsTasks,
#     summary=summary_get_points,
#     description=description_get_points,
# )
# @inject
# def get_points_by_user_id(
#     userId: UUID,
#     service: UserService = Depends(Provide[Container.user_service]),
# ):
#     return service.get_points_by_user_id(userId)


summary_preview_points = "Preview Points to Coins Conversion"
response_example_preview_points = {
    "points": 250,
    "conversionRate": 100.0,
    "conversionRateDate": "2026-02-10 16:05:00",
    "convertedAmount": 2.5,
    "convertedCurrency": "coins",
    "haveEnoughPoints": True,
}

responses_preview_points = {
    200: {
        "description": "Conversion preview calculated successfully",
        "content": {"application/json": {"example": response_example_preview_points}},
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
        "description": "User not found for provided external identifier",
        "content": {
            "application/json": {
                "example": {
                    "detail": "User not found by externalUserId: user-123"
                }
            }
        },
    },
    422: {
        "description": "Validation error in path/query parameters",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["query", "points"],
                            "msg": "value is not a valid integer",
                            "type": "type_error.integer",
                        }
                    ]
                }
            }
        },
    },
    500: {
        "description": "Internal server error while calculating conversion preview",
        "content": {
            "application/json": {
                "example": {"detail": "Points must be greater than 0"}
            }
        },
    },
}

description_preview_points = """
Calculates a preview of point-to-coin conversion for a user without creating a conversion transaction.

### Path Parameter
- `externalUserId` (`string`, required): External user identifier.

### Query Parameter
- `points` (`integer`, required): Number of points to evaluate for conversion.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns conversion preview values:
- `points`
- `conversionRate`
- `conversionRateDate`
- `convertedAmount`
- `convertedCurrency`
- `haveEnoughPoints`

### Notes
- This endpoint is read-only. Wallet balances are not modified.

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: user not found
- `422`: invalid query/path values
- `500`: preview calculation failure

<sub>**Id_endpoint:** `preview_points_to_coins_conversion`</sub>
"""  # noqa


@router.get(
    "/{externalUserId}/convert/preview",
    response_model=ResponseConversionPreview,
    summary=summary_preview_points,
    description=description_preview_points,
    responses=responses_preview_points,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def preview_points_to_coins_conversion(
    externalUserId: str,
    points: int = Query(..., description="The number of points to convert to coins"),
    service: UserService = Depends(Provide[Container.user_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Preview the conversion of points to coins for a specific user.

    Args:
        externalUserId (str): The external user ID.
        points (int): The number of points to convert.
        service (UserService): Injected UserService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): The OAuth users service.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ResponseConversionPreview: The conversion preview details.
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
                "users",
                "INFO",
                "Preview points to coins conversion - User created",
                {
                    "oauth_user_id": oauth_user_id,
                },
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
    try:
        await add_log(
            "users",
            "INFO",
            "Preview points to coins conversion",
            {"externalUserId": externalUserId, "points": points},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        response = service.preview_points_to_coins_conversion_externalUserId(
            externalUserId, points
        )
        return response
    except Exception as e:
        await add_log(
            "users",
            "ERROR",
            "Preview points to coins conversion failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise e


summary_convert_points = "Convert Points to Coins"
request_example_convert_points = {
    "points": 250,
}

response_example_convert_points = {
    "transactionId": "51d2618d-43ab-4a3c-83ec-70f2f26f7f31",
    "points": 250,
    "conversionRate": 100.0,
    "conversionRateDate": "2026-02-10 16:30:00",
    "convertedAmount": 2.5,
    "convertedCurrency": "coins",
    "haveEnoughPoints": True,
}

responses_convert_points = {
    200: {
        "description": "Points converted to coins successfully",
        "content": {"application/json": {"example": response_example_convert_points}},
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
        "description": "User not found for provided external identifier",
        "content": {
            "application/json": {
                "example": {
                    "detail": "User not found by externalUserId: user-123"
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
                            "loc": ["body", "points"],
                            "msg": "field required",
                            "type": "value_error.missing",
                        }
                    ]
                }
            }
        },
    },
    500: {
        "description": "Internal server error during conversion",
        "content": {
            "application/json": {
                "example": {"detail": "Not enough points"}
            }
        },
    },
}

description_convert_points = """
Performs the actual points-to-coins conversion for a user and persists the transaction.

### Path Parameter
- `externalUserId` (`string`, required): External user identifier.

### Request Body
- `points` (`integer`, required): Number of points to convert.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Success (200)
Returns the conversion transaction result:
- `transactionId`
- `points` (converted points)
- `conversionRate`
- `conversionRateDate`
- `convertedAmount`
- `convertedCurrency`
- `haveEnoughPoints`

### Behavior
- Wallet balances are updated (`pointsBalance` decreases, `coinsBalance` increases).
- A wallet transaction record is persisted for auditability.

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `404`: user not found
- `422`: malformed path parameters or invalid request body
- `500`: conversion failure (for example insufficient points or unexpected processing error)

<sub>**Id_endpoint:** `convert_points_to_coins`</sub>
"""  # noqa


@router.post(
    "/{externalUserId}/convert",
    response_model=ResponsePointsConversion,
    summary=summary_convert_points,
    description=description_convert_points,
    responses=responses_convert_points,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def convert_points_to_coins(
    externalUserId: str,
    schema: PostPointsConversionRequest = Body(..., example=request_example_convert_points),
    service: UserService = Depends(Provide[Container.user_actions_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Convert points to coins for a specific user.

    Args:
        externalUserId (str): The external user ID.
        schema (PostPointsConversionRequest): The schema containing conversion
          details.
        service (UserService): Injected UserService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): The OAuth users service.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ResponsePointsConversion: The conversion details.
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
                "users",
                "INFO",
                "Convert points to coins - User created",
                {
                    "oauth_user_id": oauth_user_id,
                },
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
    try:
        await add_log(
            "users",
            "INFO",
            "Convert points to coins",
            {"externalUserId": externalUserId, "schema": schema},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        response = await service.convert_points_to_coins_externalUserId(
            externalUserId, schema, api_key
        )
        return response
    except Exception as e:
        await add_log(
            "users",
            "ERROR",
            "Convert points to coins failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise e


summary_add_action_to_user = "Add Action to User"
request_example_add_action_to_user = {
    "typeAction": "LOGIN",
    "data": {
        "source": "mobile-app",
        "ip": "203.0.113.10",
    },
    "description": "User logged in from mobile app",
}

response_example_add_action_to_user = {
    "typeAction": "LOGIN",
    "description": "User logged in from mobile app",
    "userId": "8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
    "is_user_created": False,
    "message": "Action added successfully",
}

responses_add_action_to_user = {
    200: {
        "description": "User action added successfully",
        "content": {
            "application/json": {"example": response_example_add_action_to_user}
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
        "description": "Internal server error while adding user action",
        "content": {
            "application/json": {
                "example": {"detail": "Error when adding action to user"}
            }
        },
    },
}

description_add_action_to_user = """
Registers a standalone user action event for the provided `externalUserId`.

### Path Parameter
- `externalUserId` (`string`, required): External user identifier.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Request Body
- `typeAction` (`string`, required): Action/event type.
- `data` (`object`, optional): Action payload metadata.
- `description` (`string`, optional): Human-readable action description.

### Success (200)
Returns:
- `typeAction`
- `description`
- `userId` (internal id)
- `is_user_created` (`true` if user did not exist and was created automatically)
- `message`

### Notes
- If the `externalUserId` does not exist, the user is created automatically before storing the action.

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `422`: malformed path parameters or invalid request body
- `500`: action persistence failure

<sub>**Id_endpoint:** `add_action_to_user`</sub>
"""


@router.post(
    "/{externalUserId}/actions",
    response_model=CreatedUserActions,
    summary=summary_add_action_to_user,
    description=description_add_action_to_user,
    responses=responses_add_action_to_user,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def add_action_to_user(
    externalUserId: str,
    schema: CreateUserBodyActions = Body(..., example=request_example_add_action_to_user),
    service: UserActionsService = Depends(Provide[Container.user_actions_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Add an action to a specific user.

    Args:
        externalUserId (str): The external user ID.
        schema (PostPointsConversionRequest): The schema containing action
          details.
        service (UserService): Injected UserService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): The OAuth users service.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ResponsePointsConversion: The action details.
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
                "users",
                "INFO",
                "Add action to user - User created",
                {
                    "oauth_user_id": oauth_user_id,
                },
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
    try:
        await add_log(
            "users",
            "INFO",
            "Add action to user",
            {"externalUserId": externalUserId, "schema": schema},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        response = await service.user_add_action_default(
            externalUserId, schema, api_key
        )
        return response
    except Exception as e:
        await add_log(
            "users",
            "ERROR",
            "Add action to user failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        print(f"Error (add_action_to_user): {e}")
        raise e
