from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends

from app.core.container import Container
from app.core.exceptions import ForbiddenError
from app.middlewares.valid_access_token import oauth_2_scheme, valid_access_token
from app.schema.apikey_schema import (ApiKeyCreate, ApiKeyCreated,
                                      ApiKeyCreatedUnitList, ApiKeyPostBody)
from app.schema.oauth_users_schema import CreateOAuthUser
from app.services.apikey_service import ApiKeyService
from app.services.logs_service import LogsService
from app.services.oauth_users_service import OAuthUsersService
from app.util.add_log import add_log
from app.util.check_role import check_role

router = APIRouter(
    prefix="/apikey",
    tags=["API Key"],
)

summary_create_api_key = "Create API Key (Admin)"
request_example_create_api_key = {
    "client": "analytics-service",
    "description": "API key for analytics ingestion worker",
}

response_example_create_api_key = {
    "apiKey": "gk_6f7ca7f8b0e9499ea8fa6d8f6e8d2f35",
    "client": "analytics-service",
    "description": "API key for analytics ingestion worker",
    "createdBy": "11111111-2222-3333-4444-555555555555",
    "message": "API Key created successfully",
}

responses_create_api_key = {
    201: {
        "description": "API key created successfully",
        "content": {"application/json": {"example": response_example_create_api_key}},
    },
    401: {
        "description": "Unauthorized: missing, invalid, or expired bearer token",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: token is valid but user lacks `AdministratorGAME` role",
        "content": {
            "application/json": {
                "example": {
                    "detail": "You do not have permission to create an API key"
                }
            }
        },
    },
    422: {
        "description": "Validation error in request body",
    },
    500: {
        "description": "Internal server error while creating API key",
    },
}

description_create_api_key = """
Creates a new API key for a client integration.

### Authorization
- Requires `Authorization: Bearer <access_token>`.
- Caller must have role `AdministratorGAME` (checked from JWT roles).

### Request Body
- `client` (`string`): Identifier of the consuming client/service.
- `description` (`string`): Human-readable purpose for traceability.

### Success (201)
Returns the generated API key and metadata (`client`, `description`, `createdBy`).

### Error Cases
- `401`: missing/invalid/expired token
- `403`: authenticated user without admin role
- `422`: invalid request payload

<sub>**Id_endpoint:** `create_api_key`</sub>
"""  # noqa


@router.post(
    "/create",
    summary=summary_create_api_key,
    description=description_create_api_key,
    response_description="API Key created successfully",
    response_model=ApiKeyCreated,
    status_code=201,
    responses=responses_create_api_key,
    dependencies=[Depends(oauth_2_scheme)],
)
@inject
async def create_api_key(
    schema: ApiKeyPostBody = Body(..., example=request_example_create_api_key),
    service: ApiKeyService = Depends(Provide[Container.apikey_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Endpoint to create an API key, requires authentication.

    Args:
        schema (ApiKeyPostBody): The API key schema.
        service (ApiKeyService): The API key service.
        service_log (LogsService): The logs service.
        service_oauth (OAuthUsersService): The OAuth users service.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ApiKeyCreated: The API key created response.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    token_decoded = await valid_access_token(token)
    if token_decoded.error:
        await add_log(
            "api_key",
            "ERROR",
            "Error creating API key",
            {
                "client": schema.client,
                "description": schema.description,
                "error": str(token_decoded.error),
            },
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )

        raise token_decoded.error
    if token_decoded.data:
        oauth_user_id = token_decoded.data["sub"]
        existing_user = await service_oauth.get_user_by_sub(oauth_user_id)
        if existing_user is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "api_key",
                "INFO",
                "Creating API key - User created",
                {
                    "client": schema.client,
                    "description": schema.description,
                    "oauth_user_id": oauth_user_id,
                },
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
    await add_log(
        "api_key",
        "INFO",
        "Creating API key",
        {"client": schema.client, "description": schema.description},
        service_log,
        api_key=api_key,
        oauth_user_id=str(oauth_user_id),
    )

    token_decoded = token_decoded.data

    if not check_role(token_decoded, "AdministratorGAME"):
        await add_log(
            "api_key",
            "ERROR",
            "Error creating API key",
            {
                "client": schema.client,
                "description": schema.description,
                "error": "You do not have permission to create an API key",
            },
            service_log,
            api_key=api_key,
            oauth_user_id=str(oauth_user_id),
        )
        raise ForbiddenError("You do not have permission to create an API key")
    apiKey = await service.generate_api_key_service()
    apikeyBody = ApiKeyCreate(**schema.dict(), createdBy=oauth_user_id, apiKey=apiKey)
    try:
        response = await service.create_api_key(apikeyBody)
        await add_log(
            "api_key",
            "SUCCESS",
            "API key created successfully",
            {
                "client": schema.client,
                "description": schema.description,
                "apiKey": apiKey,
            },
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        return ApiKeyCreated(**response.dict(), message="API Key created successfully")
    except Exception as e:
        await add_log(
            "api_key",
            "ERROR",
            "Error creating API key",
            {
                "client": schema.client,
                "description": schema.description,
                "error": str(e),
            },
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise e


summary_get_all_api_keys = "List API Keys (Admin)"
response_example_get_all_api_keys = [
    {
        "apiKey": "gk_6f7ca7f8b0e9499ea8fa6d8f6e8d2f35",
        "client": "analytics-service",
        "description": "API key for analytics ingestion worker",
        "createdBy": "11111111-2222-3333-4444-555555555555",
        "created_at": "2026-02-10T12:00:00Z",
    },
    {
        "apiKey": "gk_90d4f6bd39b141eb9a4e3ca33211e2d7",
        "client": "mobile-app-backend",
        "description": "Key used by mobile backend services",
        "createdBy": "99999999-aaaa-bbbb-cccc-dddddddddddd",
        "created_at": "2026-02-09T09:30:00Z",
    },
]

responses_get_all_api_keys = {
    200: {
        "description": "List of API keys retrieved successfully",
        "content": {"application/json": {"example": response_example_get_all_api_keys}},
    },
    401: {
        "description": "Unauthorized: missing, invalid, or expired bearer token",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: token is valid but user lacks `AdministratorGAME` role",
        "content": {
            "application/json": {
                "example": {
                    "detail": "You do not have permission to get all API keys"
                }
            }
        },
    },
    500: {
        "description": "Internal server error while retrieving API keys",
    },
}

description_get_all_api_keys = """
Returns the full list of API keys registered in the system.

### Authorization
- Requires `Authorization: Bearer <access_token>`.
- Caller must have role `AdministratorGAME`.

### Success (200)
Returns an array of API keys with metadata:
- `apiKey`
- `client`
- `description`
- `createdBy`
- `created_at`

### Error Cases
- `401`: missing/invalid/expired token
- `403`: authenticated user without admin role

<sub>**Id_endpoint:** `get_all_api_keys`</sub>
"""  # noqa


@router.get(
    "",
    summary=summary_get_all_api_keys,
    description=description_get_all_api_keys,
    response_description="API Keys retrieved successfully",
    response_model=List[ApiKeyCreatedUnitList],
    status_code=200,
    responses=responses_get_all_api_keys,
    dependencies=[Depends(oauth_2_scheme)],
)
@inject
async def get_all_api_keys(
    service: ApiKeyService = Depends(Provide[Container.apikey_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Endpoint to get all API keys, requires authentication.

    Args:
        service (ApiKeyService): The API key service.
        service_log (LogsService): The logs service.
        service_oauth (OAuthUsersService): The OAuth users service.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[ApiKeyCreatedUnitList]: The list of all API keys.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    token_decoded = await valid_access_token(token)
    if token_decoded.error:
        await add_log(
            "api_key",
            "ERROR",
            "Error getting all API keys",
            {
                "error": str(token_decoded.error),
            },
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise token_decoded.error

    token_decoded_data = token_decoded.data
    if token_decoded_data:
        oauth_user_id = token_decoded_data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "api_key",
                "INFO",
                "Getting all API keys - User created",
                {},
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
    if not check_role(token_decoded_data, "AdministratorGAME"):
        await add_log(
            "api_key",
            "ERROR",
            "Error getting all API keys",
            {
                "error": "You do not have permission to get all API keys",
            },
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise ForbiddenError("You do not have permission to get all API keys")
    await add_log(
        "api_key",
        "INFO",
        "Getting all API keys",
        {},
        service_log,
        api_key=api_key,
        oauth_user_id=oauth_user_id,
    )
    return service.get_all_api_keys()
