from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends

from app.core.container import Container
from app.middlewares.valid_access_token import oauth_2_scheme, valid_access_token
from app.schema.apikey_schema import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyCreatedUnitList,
    ApiKeyPostBody,
)
from app.services.apikey_service import ApiKeyService
from app.services.logs_service import LogsService
from app.util.check_role import check_role
from app.core.exceptions import ForbiddenError
from app.util.add_log import add_log

router = APIRouter(
    prefix="/apikey",
    tags=["API Key"],
)

summary_create_api_key = "Create an API key"
description_create_api_key = """
## Create an API key
### This endpoint allows you to create an API key. You must be authenticated to create an API key. 
<sub>**Id_endpoint:** create_api_key</sub>
"""  # noqa


@router.post(
    "/create",
    summary=summary_create_api_key,
    description=description_create_api_key,
    response_description="API Key created successfully",
    response_model=ApiKeyCreated,
    status_code=201,
    dependencies=[Depends(oauth_2_scheme)],
)
@inject
async def create_api_key(
    schema: ApiKeyPostBody = Body(...),
    service: ApiKeyService = Depends(Provide[Container.apikey_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Endpoint to create an API key, requires authentication.

    Args:
        schema (ApiKeyPostBody): The API key schema.
        service (ApiKeyService): The API key service.
        service_log (LogsService): The logs service.
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
                "error": token_decoded.error,
            },
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )

        raise token_decoded.error
    if token_decoded.data:
        oauth_user_id = token_decoded.data["sub"]
    await add_log(
        "api_key",
        "INFO",
        "Creating API key",
        {"client": schema.client, "description": schema.description},
        service_log,
        api_key=api_key,
        oauth_user_id=oauth_user_id,
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
            oauth_user_id=oauth_user_id,
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


summary_get_all_api_keys = "Get all API keys"
description_get_all_api_keys = """
## Get all API keys
### This endpoint allows you to get all API keys. You must be authenticated to get all API keys.
<sub>**Id_endpoint:** get_all_api_keys</sub>
"""  # noqa


@router.get(
    "",
    summary=summary_get_all_api_keys,
    description=description_get_all_api_keys,
    response_description="API Keys retrieved successfully",
    response_model=List[ApiKeyCreatedUnitList],
    status_code=200,
    dependencies=[Depends(oauth_2_scheme)],
)
@inject
async def get_all_api_keys(
    service: ApiKeyService = Depends(Provide[Container.apikey_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Endpoint to get all API keys, requires authentication.
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
                "error": token_decoded.error,
            },
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise token_decoded.error

    token_decoded_data = token_decoded.data
    if token_decoded_data:
        oauth_user_id = token_decoded_data["sub"]
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
