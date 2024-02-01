from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from uuid import UUID
from app.core.container import Container

from app.schema.user_schema import (
    PostCreateUser,
    CreatedUser,
    PostAssignPointsToUser,
    UserWallet,
    UserPointsTasks,
    ConversionPreviewResponse
)
from app.schema.user_points_schema import (
    UserPointsAssigned,
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
    response_model=UserPointsAssigned,
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


summary_get_wallet_by_user_id = "Get wallet by user id"
description_get_wallet_by_user_id = """
## Get wallet by user id
### Get wallet by user id
"""

summary_get_points = "Get points by user id"
description_get_points = """
## Get points by user id
### Get points by user id
"""


@router.get(
    "/{userId}/points",
    response_model=UserPointsTasks,
    summary=summary_get_points,
    description=description_get_points,
)
@inject
def get_points_by_user_id(
    userId: UUID,
    service: UserService = Depends(
        Provide[Container.user_service]),
):
    return service.get_points_by_user_id(userId)


@router.get(
    "/{userId}/wallet",
    response_model=UserWallet,
    summary=summary_get_wallet_by_user_id,
    description=description_get_wallet_by_user_id,
)
@inject
def get_wallet_by_user_id(
    userId: UUID,
    service: UserService = Depends(
        Provide[Container.user_service]),
):
    return service.get_wallet_by_user_id(userId)


summary_preview_points = "Preview Points to Coins Conversion"
description_preview_points = """## Preview Points to Coins Conversion
### Provides a preview of the points to coins conversion for a specific user. """


@router.get(
    "/{userId}/convert/preview",
    response_model=ConversionPreviewResponse,
    summary=summary_preview_points,
    description=description_preview_points,
)
@inject
def preview_points_to_coins_conversion(
    userId: UUID,
    points: int = Query(...,
                        description="The number of points to convert to coins"),
    service: UserService = Depends(Provide[Container.user_service]),
):
    return service.preview_points_to_coins_conversion(userId, points)


summary_convert_points = "Convert Points to Coins"
description_convert_points = """## Convert Points to Coins
### Performs the actual conversion of points to coins for the specified user.
"""

@router.post(
    "/{userId}/convert",
    response_model=UserWallet,
    summary=summary_convert_points,
    description=description_convert_points,
)
@inject
def convert_points_to_coins(
    userId: UUID,
    schema: PointsConversionRequest,
    service: UserService = Depends(Provide[Container.user_service]),
):
    # Logic to perform conversion should be implemented in UserService or a dedicated service.
    return service.convert_points_to_coins(userId, schema)
