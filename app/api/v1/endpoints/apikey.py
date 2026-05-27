from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Path

from app.core.container import Container
from app.core.exceptions import ForbiddenError, NotFoundError
from app.middlewares.auth_context import AuditLogger, audit_log
from app.middlewares.authentication import auth_oauth2
from app.schema.apikey_schema import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyCreatedUnitList,
    ApiKeyPostBody,
    ApiKeyRevoked,
)
from app.services.apikey_service import ApiKeyService

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
    "apiKey": "gme_live_3f6a9e0f",
    "plaintext": "gme_live_3f6a9e0f.AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEf",
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
        "description": ("Unauthorized: missing, invalid, or expired bearer token"),
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": (
            "Forbidden: token is valid but user lacks `AdministratorGAME` " "role"
        ),
        "content": {
            "application/json": {
                "example": {"detail": "You do not have permission to create an API key"}
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
Returns the generated key. The `plaintext` field is the **only** time the
full secret is shown -- the server stores only the sha256 hash and the
public prefix, so it cannot be recovered later. The `apiKey` field is the
public prefix, which is what appears in audit logs.

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
    dependencies=[Depends(auth_oauth2)],
)
@inject
async def create_api_key(
    schema: ApiKeyPostBody = Body(..., examples=[request_example_create_api_key]),
    service: ApiKeyService = Depends(Provide[Container.apikey_service]),
    audit: AuditLogger = Depends(audit_log("api_key")),
):
    """
    Endpoint to create an API key, requires authentication.

    Args:
        schema (ApiKeyPostBody): The API key schema.
        service (ApiKeyService): The API key service.
        audit (AuditLogger): Per-request audit logger bound to the auth context.

    Returns:
        ApiKeyCreated: The API key created response.
    """
    auth = audit.auth
    await audit.info(
        "Creating API key",
        {"client": schema.client, "description": schema.description},
    )

    if not auth.is_admin:
        await audit.error(
            "Error creating API key",
            {
                "client": schema.client,
                "description": schema.description,
                "error": ("You do not have permission to create an API key"),
            },
        )
        raise ForbiddenError("You do not have permission to create an API key")
    generated = await service.generate_api_key_service()
    apikeyBody = ApiKeyCreate(
        **schema.model_dump(),
        createdBy=auth.oauth_user_id,
        apiKey=generated.prefix,
        apiKeyHash=generated.key_hash,
    )
    try:
        response = await service.create_api_key(apikeyBody)
        await audit.success(
            "API key created successfully",
            {
                "client": schema.client,
                "description": schema.description,
                "apiKey": generated.prefix,
            },
        )
        response_dict = response.model_dump()
        response_dict.pop("apiKeyHash", None)
        return ApiKeyCreated(
            **response_dict,
            plaintext=generated.plaintext,
            message="API Key created successfully",
        )
    except Exception as e:
        await audit.error(
            "Error creating API key",
            {
                "client": schema.client,
                "description": schema.description,
                "error": str(e),
            },
        )
        raise e


summary_get_all_api_keys = "List API Keys (Admin)"
response_example_get_all_api_keys = [
    {
        "apiKey": "gme_live_3f6a9e0f",
        "client": "analytics-service",
        "description": "API key for analytics ingestion worker",
        "createdBy": "11111111-2222-3333-4444-555555555555",
        "created_at": "2026-02-10T12:00:00Z",
        "active": True,
    },
    {
        "apiKey": "gme_live_90d4f6bd",
        "client": "mobile-app-backend",
        "description": "Key used by mobile backend services",
        "createdBy": "99999999-aaaa-bbbb-cccc-dddddddddddd",
        "created_at": "2026-02-09T09:30:00Z",
        "active": True,
    },
]

responses_get_all_api_keys = {
    200: {
        "description": "List of API keys retrieved successfully",
        "content": {"application/json": {"example": response_example_get_all_api_keys}},
    },
    401: {
        "description": ("Unauthorized: missing, invalid, or expired bearer token"),
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": (
            "Forbidden: token is valid but user lacks `AdministratorGAME` " "role"
        ),
        "content": {
            "application/json": {
                "example": {"detail": "You do not have permission to get all API keys"}
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
Returns an array of API key records with metadata:
- `apiKey` (public prefix; the secret itself is never returned)
- `client`
- `description`
- `createdBy`
- `created_at`
- `active`

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
    dependencies=[Depends(auth_oauth2)],
)
@inject
async def get_all_api_keys(
    service: ApiKeyService = Depends(Provide[Container.apikey_service]),
    audit: AuditLogger = Depends(audit_log("api_key")),
):
    """
    Endpoint to get all API keys, requires authentication.

    Args:
        service (ApiKeyService): The API key service.
        audit (AuditLogger): Per-request audit logger bound to the auth context.

    Returns:
        List[ApiKeyCreatedUnitList]: The list of all API keys.
    """
    if not audit.auth.is_admin:
        await audit.error(
            "Error getting all API keys",
            {
                "error": ("You do not have permission to get all API keys"),
            },
        )
        raise ForbiddenError("You do not have permission to get all API keys")
    await audit.info("Getting all API keys")
    return await service.get_all_api_keys()


summary_revoke_api_key = "Revoke API Key (Admin)"
responses_revoke_api_key = {
    200: {
        "description": "API key revoked successfully",
        "content": {
            "application/json": {
                "example": {
                    "apiKey": "gme_live_3f6a9e0f",
                    "active": False,
                    "message": "API key revoked successfully.",
                }
            }
        },
    },
    401: {"description": "Unauthorized"},
    403: {"description": "Forbidden -- caller is not an admin"},
    404: {"description": "API key prefix does not exist"},
}

description_revoke_api_key = """
Revokes an API key by its public prefix (e.g. `gme_live_3f6a9e0f`).

The prefix is the safe identifier that appears in audit logs; the secret
itself is never accepted on this endpoint. Revocation deactivates the row
(``active=false``) and clears the in-memory authentication cache so the
key stops working on subsequent requests.

### Authorization
- Requires `Authorization: Bearer <access_token>`.
- Caller must have role `AdministratorGAME`.

<sub>**Id_endpoint:** `revoke_api_key`</sub>
"""  # noqa


@router.delete(
    "/{prefix}",
    summary=summary_revoke_api_key,
    description=description_revoke_api_key,
    response_description="API key revoked successfully",
    response_model=ApiKeyRevoked,
    status_code=200,
    responses=responses_revoke_api_key,
    dependencies=[Depends(auth_oauth2)],
)
@inject
async def revoke_api_key(
    prefix: str = Path(..., description="Public prefix of the API key to revoke."),
    service: ApiKeyService = Depends(Provide[Container.apikey_service]),
    audit: AuditLogger = Depends(audit_log("api_key")),
):
    """
    Endpoint to revoke an API key by its public prefix.
    """
    if not audit.auth.is_admin:
        await audit.error(
            "Error revoking API key",
            {
                "prefix": prefix,
                "error": ("You do not have permission to revoke an API key"),
            },
        )
        raise ForbiddenError("You do not have permission to revoke an API key")

    try:
        revoked = await service.revoke_api_key_by_prefix(prefix)
    except NotFoundError as exc:
        await audit.error(
            "Error revoking API key",
            {"prefix": prefix, "error": str(exc.detail)},
        )
        raise exc

    await audit.success("API key revoked successfully", {"prefix": prefix})
    return ApiKeyRevoked(
        apiKey=revoked.apiKey,
        active=bool(revoked.active),
        message="API key revoked successfully.",
    )
