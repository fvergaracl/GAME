from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.user_points_schema import (
    FindQueryByExternalGameId,
    FindAllUserPointsResult,

)

from app.schema.user_schema import (
    PostCreateUser,
    CreatedUser
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
