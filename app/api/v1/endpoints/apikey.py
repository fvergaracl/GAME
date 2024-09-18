from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends

from app.core.container import Container
from app.middlewares.valid_access_token import (
    oauth_2_scheme, valid_access_token
)
from app.schema.apikey_schema import (
    ApiKeyCreate, ApiKeyCreated,  ApiKeyCreatedUnitList, ApiKeyPostBody
)
from app.services.apikey_service import ApiKeyService
from app.util.check_role import check_role
from app.core.exceptions import ForbiddenError

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
    token: str = Depends(oauth_2_scheme),
):
    """
    Endpoint to create an API key, requires authentication.
    """
    token_decoded = await valid_access_token(token)
    token_decoded = token_decoded.data
    if not check_role(token_decoded, "AdministratorGAME"):
        raise ForbiddenError("You do not have permission to create an API key")
    created_by = token_decoded["sub"]
    apiKey = await service.generate_api_key_service()
    apikeyBody = ApiKeyCreate(**schema.dict(),
                              createdBy=created_by,
                              apiKey=apiKey)
    response = service.create_api_key(apikeyBody)

    return ApiKeyCreated(**response.dict(),
                         message="API Key created successfully")


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
    token: str = Depends(oauth_2_scheme),
):
    """
    Endpoint to get all API keys, requires authentication.
    """
    token_decoded = await valid_access_token(token)
    token_decoded_error = token_decoded.error
    token_decoded_data = token_decoded.data
    if token_decoded_error:
        raise token_decoded_error
    if not check_role(token_decoded_data, "AdministratorGAME"):
        raise ForbiddenError("You do not have permission to get all API keys")
    await valid_access_token(token)
    return service.get_all_api_keys()
