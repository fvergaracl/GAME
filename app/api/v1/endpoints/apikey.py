from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Body
from app.schema.apikey_schema import (
    ApiKeyCreated, ApiKeyPostBody, ApiKeyCreate
)
from app.services.apikey_service import ApiKeyService
from app.core.container import Container

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
)
@inject
async def create_api_key(
    schema: ApiKeyPostBody = Body(...),
    service: ApiKeyService = Depends(Provide[Container.apikey_service]),
):
    """
    Endpoint to create an API key, requires authentication.
    """
    created_by = "admin"
    apikeyBody = ApiKeyCreate(**schema.dict(), createdBy=created_by)
    return await service.create_api_key(apikeyBody)
