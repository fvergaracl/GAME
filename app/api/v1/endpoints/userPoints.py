from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.user_points_schema import (
    FindQueryByExternalGameId,
    FindAllUserPointsResult
)
from app.services.user_points_service import UserPointsService

router = APIRouter(
    prefix="/points",
    tags=["points"],
)


@router.get("/{externalGameId}", response_model=FindAllUserPointsResult)
@inject
def get_users_points_by_externalGameId(
    schema: FindQueryByExternalGameId = Depends(),
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    externalGameId = schema.externalGameId
    return service.get_users_points_by_externalGameId(externalGameId)
