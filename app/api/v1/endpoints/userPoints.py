from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.user_points_schema import (
    FindQueryByExternalGameId,
    FindAllUserPointsResult,
    FindQueryByExternalTaskId,
    FindQueryByExternalTaskIdExternalUserId,
    PostAssignPointsToUser,
    ResponseAssignPointsToUser
)
from app.services.user_points_service import UserPointsService

router = APIRouter(
    prefix="/points",
    tags=["points"],
)


@router.get("/game/{externalGameId}", response_model=FindAllUserPointsResult)
@inject
def get_users_points_by_externalGameId(
    schema: FindQueryByExternalGameId = Depends(),
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    externalGameId = schema.externalGameId
    return service.get_users_points_by_externalGameId(externalGameId)


@router.get("/task/{externalTaskId}", response_model=FindAllUserPointsResult)
@inject
def get_users_points_by_externalTaskId(
    schema: FindQueryByExternalTaskId = Depends(),
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    externalTaskId = schema.externalTaskId
    return service.get_users_points_by_externalTaskId(externalTaskId)


@router.get("/task/{externalTaskId}/user/{externalUserId}", response_model=FindAllUserPointsResult)
@inject
def get_users_points_by_externalTaskId_and_externalUserId(
    schema: FindQueryByExternalTaskIdExternalUserId = Depends(),
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    externalTaskId = schema.externalTaskId
    externalUserId = schema.externalUserId
    return service.get_users_points_by_externalTaskId_and_externalUserId(externalTaskId, externalUserId)


@router.post("/assign", response_model=ResponseAssignPointsToUser)
@inject
def assign_points_to_user(
    schema: PostAssignPointsToUser,
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    return service.assign_points_to_user(schema)
