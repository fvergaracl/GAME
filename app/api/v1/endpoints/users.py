from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from uuid import UUID
from app.core.container import Container

from app.schema.user_schema import (
    PostCreateUser,
    CreatedUser,
    PostAssignPointsToUser,
    PointsAssignedToUser,
)
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


# create user
@router.post("/", response_model=CreatedUser)
@inject
def create_user(
    schema: PostCreateUser,
    service: UserService = Depends(
        Provide[Container.user_service]),
):
    return service.create_user(schema)


summary_assign_points_to_user = "Assign points to user"
description_assign_points_to_user = """
## Assign points to user
### Assign points to user
"""


@router.post(
    "/{userId}/points",
    response_model=PointsAssignedToUser,
    summary=summary_assign_points_to_user,
    description=description_assign_points_to_user,

)
@inject
def assign_points_to_user(
    userId: UUID,
    schema: PostAssignPointsToUser,
    service: UserService = Depends(
        Provide[Container.user_service]),
):
    return service.assign_points_to_user(userId, schema)
