from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from typing import List
from app.core.container import Container
from app.schema.user_points_schema import (
    FindQueryByExternalGameId,
    FindAllUserPointsResult,
    FindQueryByExternalTaskId,
    FindQueryByExternalTaskIdExternalUserId,
    PostAssignPointsToUser,
    ResponseAssignPointsToUser,
    ResponsePointsByExternalUserId,
    ResponseGetPointsByTask,
    ResponseGetPointsByGame
)
from app.services.user_points_service import UserPointsService

router = APIRouter(
    prefix="/points",
    tags=["points"],
)


@router.get("/game/{externalGameId}", response_model=List[ResponseGetPointsByGame])
@inject
def get_users_points_by_externalGameId(
    schema: FindQueryByExternalGameId = Depends(),
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    externalGameId = schema.externalGameId
    return service.get_users_points_by_externalGameId(externalGameId)


@router.get("/task/{externalTaskId}", response_model=List[ResponseGetPointsByTask])
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

# get points of a user


@router.get("/user/{externalUserId}", response_model=ResponsePointsByExternalUserId)
@inject
def get_points_of_user(
    schema: FindQueryByExternalTaskIdExternalUserId = Depends(),
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    externalUserId = schema.externalUserId
    return service.get_points_of_user(externalUserId)
