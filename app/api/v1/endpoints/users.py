from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from typing import List
from app.core.container import Container
from app.schema.user_points_schema import AllPointsByGame
from app.schema.user_schema import (
    PostPointsConversionRequest, ResponseConversionPreview,
    ResponsePointsConversion, UserWallet
)
from app.services.user_service import UserService
from app.services.user_points_service import UserPointsService, UserGamePoints

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

"""
/users/points/query:
  post:
    tags:
      - users
    summary: Query User Points
    description: |
      ## Query User Points
      This endpoint retrieves the point totals for a list of users based on their external user IDs. This operation does not modify any user data.
    operationId: query_user_points
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              externalUserIds:
                type: array
                items:
                  type: string
            example:
              externalUserIds: ["user1", "user2", "user3"]
    responses:
      200:
        description: Successful response with point details for each user.
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  externalUserId:
                    type: string
                  points:
                    type: integer
              example:
                - externalUserId: "user1"
                  points: 120
                - externalUserId: "user2"
                  points: 150
                - externalUserId: "user3"
                  points: 90
      400:
        description: Bad request if the request body is not properly formatted.

"""

summary_query_user_points = "Query User Points"
description_query_user_points = """
## Query User Points
This endpoint retrieves the point totals for a list of users based on their external user IDs. This operation does not modify any user data.
"""


@router.post(
    "/points/query",
    response_model=List[UserGamePoints],
    summary=summary_query_user_points,
    description=description_query_user_points,
)
@inject
def query_user_points(
    schema: List[str],
    service: UserPointsService = Depends(
        Provide[Container.user_points_service])
):
    response = service.get_points_by_user_list(schema)
    print('******************************************************')
    print('******************************************************')
    print('******************************************************')
    print('******************************************************')
    print('******************************************************')
    print(response)
    print('******************************************************')
    print('******************************************************')
    print('******************************************************')
    print('******************************************************')
    print('******************************************************')
    return response


summary_get_user_points = "Get user points"
description_get_user_points = """
## Get user points
### Get user points
"""


@ router.get(
    "/{externalUserId}/points",
    response_model=List[AllPointsByGame],
    summary=summary_get_user_points,
    description=description_get_user_points,
)
@ inject
def get_points_by_user_id(
    externalUserId: str,
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    return service.get_points_by_externalUserId(externalUserId)


summary_get_user_wallet = "Get user wallet"
description_get_user_wallet = """
## Get user wallet
### Get user wallet
"""


@ router.get(
    "/{externalUserId}/wallet",
    response_model=UserWallet,
    summary=summary_get_user_wallet,
    description=description_get_user_wallet,
)
@ inject
def get_wallet_by_user_id(
    externalUserId: str,
    service: UserService = Depends(Provide[Container.user_service]),
):
    return service.get_wallet_by_externalUserId(externalUserId)


# @router.get("")
# @inject
# def list_users(
#     schema: FindBase = Depends(),
#     service: UserService = Depends(Provide[Container.user_service]),
# ):
#     return service.get_list(schema)


# @router.post("", response_model=CreatedUser)
# @inject
# def create_user(
#     schema: PostCreateUser,
#     service: UserService = Depends(Provide[Container.user_service]),
# ):
#     return service.create_user(schema)


# summary_assign_points_to_user = "Assign points to user"
# description_assign_points_to_user = """
# ## Assign points to user
# ### Assign points to user
# """


# @router.post(
#     "/{userId}/points",
#     response_model=UserPointsAssigned,
#     summary=summary_assign_points_to_user,
#     description=description_assign_points_to_user,
# )
# @inject
# def assign_points_to_user(
#     userId: UUID,
#     schema: PostAssignPointsToUser,
#     service: UserService = Depends(Provide[Container.user_service]),
# ):
#     return service.assign_points_to_user(userId, schema)


# summary_get_points = "Get points by user id"
# description_get_points = """
# ## Get points by user id
# ### Get points by user id
# """


# @router.get(
#     "/{userId}/points",
#     response_model=UserPointsTasks,
#     summary=summary_get_points,
#     description=description_get_points,
# )
# @inject
# def get_points_by_user_id(
#     userId: UUID,
#     service: UserService = Depends(Provide[Container.user_service]),
# ):
#     return service.get_points_by_user_id(userId)


summary_preview_points = "Preview Points to Coins Conversion"
description_preview_points = """## Preview Points to Coins Conversion
### Provides a preview of the points to coins conversion for a specific user.
"""


@ router.get(
    "/{externalUserId}/convert/preview",
    response_model=ResponseConversionPreview,
    summary=summary_preview_points,
    description=description_preview_points,
)
@ inject
def preview_points_to_coins_conversion(
    externalUserId: str,
    points: int = Query(...,
                        description="The number of points to convert to coins"),
    service: UserService = Depends(Provide[Container.user_service]),
):
    return service.preview_points_to_coins_conversion_externalUserId(
        externalUserId, points
    )


summary_convert_points = "Convert Points to Coins"
description_convert_points = """## Convert Points to Coins
### Performs the actual conversion of points to coins for the specified user.
"""


@ router.post(
    "/{externalUserId}/convert",
    response_model=ResponsePointsConversion,
    summary=summary_convert_points,
    description=description_convert_points,
)
@ inject
def convert_points_to_coins(
    externalUserId: str,
    schema: PostPointsConversionRequest,
    service: UserService = Depends(Provide[Container.user_service]),
):
    return service.convert_points_to_coins_externalUserId(externalUserId, schema)
