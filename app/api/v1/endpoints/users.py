from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from app.services.logs_service import LogsService
from app.services.apikey_service import ApiKeyService
from app.middlewares.valid_access_token import oauth_2_scheme, valid_access_token
from app.util.add_log import add_log
from app.core.container import Container
from app.schema.user_points_schema import AllPointsByGame, UserGamePoints
from app.schema.user_schema import (
    PostPointsConversionRequest,
    ResponseConversionPreview,
    ResponsePointsConversion,
    UserWallet,
)
from app.schema.user_actions_schema import CreateUserBodyActions, CreatedUserActions
from app.services.user_points_service import UserPointsService
from app.services.user_service import UserService
from app.services.user_actions_service import UserActionsService
from app.middlewares.authentication import auth_api_key_or_oauth2

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
      This endpoint retrieves the point totals for a list of users based on
        their external user IDs. This operation does not modify any user data.
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

summary_query_user_points = "Query User Points by External IDs"
description_query_user_points = """
## Query User Points by External IDs
### This endpoint retrieves the total points for a list of users based on their external user IDs. No user data is modified by this operation. 
<sub>**Id_endpoint:** query_user_points</sub>
"""  # noqa


@router.post(
    "/points/query",
    response_model=List[UserGamePoints],
    summary=summary_query_user_points,
    description=description_query_user_points,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def query_user_points(
    schema: List[str],
    service: UserPointsService = Depends(Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve point totals for a list of users based on their external user IDs.

    Args:
        schema (List[str]): A list of external user IDs.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[UserGamePoints]: The point details for each user.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauthusers_id = None
    if token:
        token_data = await valid_access_token(token)
        oauthusers_id = token_data.data["sub"]
    try:
        await add_log(
            "users",
            "INFO",
            "Query user points",
            {"externalUserIds": schema},
            service_log,
            api_key=api_key,
            oauth_user_id=oauthusers_id,
        )
        response = service.get_points_by_user_list(schema)
        return response
    except Exception as e:
        await add_log(
            "users",
            "ERROR",
            "Query user points failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauthusers_id,
        )
        raise e


summary_get_user_points = "Retrieve User Points"
description_get_user_points = """
## Retrieve User Points
### This endpoint retrieves the points details associated with a specific user using their external user ID. 
<sub>**Id_endpoint:** get_user_points</sub>
"""  # noqa


@router.get(
    "/{externalUserId}/points",
    response_model=List[AllPointsByGame],
    summary=summary_get_user_points,
    description=description_get_user_points,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_by_user_id(
    externalUserId: str,
    service: UserPointsService = Depends(Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve points associated with a user by their external user ID.

    Args:
        externalUserId (str): The external user ID.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[AllPointsByGame]: The points details for the specified user.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauthusers_id = None
    if token:
        token_data = await valid_access_token(token)
        oauthusers_id = token_data.data["sub"]
    try:
        await add_log(
            "users",
            "INFO",
            "Get user points",
            {"externalUserId": externalUserId},
            service_log,
            api_key=api_key,
            oauth_user_id=oauthusers_id,
        )
        response = service.get_points_by_externalUserId(externalUserId)
        return response
    except Exception as e:
        await add_log(
            "users",
            "ERROR",
            "Get user points failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauthusers_id,
        )
        raise e


summary_get_user_wallet = "Retrieve User Wallet"
description_get_user_wallet = """
## Retrieve User Wallet
### This endpoint retrieves the wallet details associated with a specific user using their external user ID. 
<sub>**Id_endpoint:** get_user_wallet</sub>"""  # noqa


@router.get(
    "/{externalUserId}/wallet",
    response_model=UserWallet,
    summary=summary_get_user_wallet,
    description=description_get_user_wallet,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_wallet_by_user_id(
    externalUserId: str,
    service: UserService = Depends(Provide[Container.user_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve the wallet details associated with a user by their external user
      ID.

    Args:
        externalUserId (str): The external user ID.
        service (UserService): Injected UserService dependency.
        service_log (LogsService): Injected LogsService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        UserWallet: The wallet details for the specified user.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauthusers_id = None
    if token:
        token_data = await valid_access_token(token)
        oauthusers_id = token_data.data["sub"]
    try:
        await add_log(
            "users",
            "INFO",
            "Get user wallet",
            {"externalUserId": externalUserId},
            service_log,
            api_key=api_key,
            oauth_user_id=oauthusers_id,
        )
        response = service.get_wallet_by_externalUserId(externalUserId)
        return response
    except Exception as e:
        await add_log(
            "users",
            "ERROR",
            "Get user wallet failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauthusers_id,
        )
        raise e


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
description_preview_points = """
## Preview Points to Coins Conversion
### This endpoint provides a preview of the conversion from points to coins for a specific user. 
<sub>**Id_endpoint:** preview_points_to_coins_conversion</sub>
"""  # noqa


@router.get(
    "/{externalUserId}/convert/preview",
    response_model=ResponseConversionPreview,
    summary=summary_preview_points,
    description=description_preview_points,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def preview_points_to_coins_conversion(
    externalUserId: str,
    points: int = Query(..., description="The number of points to convert to coins"),
    service: UserService = Depends(Provide[Container.user_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Preview the conversion of points to coins for a specific user.

    Args:
        externalUserId (str): The external user ID.
        points (int): The number of points to convert.
        service (UserService): Injected UserService dependency.
        service_log (LogsService): Injected LogsService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ResponseConversionPreview: The conversion preview details.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauthusers_id = None
    if token:
        token_data = await valid_access_token(token)
        oauthusers_id = token_data.data["sub"]
    try:
        await add_log(
            "users",
            "INFO",
            "Preview points to coins conversion",
            {"externalUserId": externalUserId, "points": points},
            service_log,
            api_key=api_key,
            oauth_user_id=oauthusers_id,
        )
        response = service.preview_points_to_coins_conversion_externalUserId(
            externalUserId, points
        )
        return response
    except Exception as e:
        await add_log(
            "users",
            "ERROR",
            "Preview points to coins conversion failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauthusers_id,
        )
        raise e


summary_convert_points = "Convert Points to Coins"
description_convert_points = """
## Convert Points to Coins
### This endpoint performs the actual conversion of points to coins for the specified user. 
<sub>**Id_endpoint:** convert_points_to_coins</sub>
"""  # noqa


@router.post(
    "/{externalUserId}/convert",
    response_model=ResponsePointsConversion,
    summary=summary_convert_points,
    description=description_convert_points,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def convert_points_to_coins(
    externalUserId: str,
    schema: PostPointsConversionRequest,
    service: UserService = Depends(Provide[Container.user_actions_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Convert points to coins for a specific user.

    Args:
        externalUserId (str): The external user ID.
        schema (PostPointsConversionRequest): The schema containing conversion
          details.
        service (UserService): Injected UserService dependency.
        service_log (LogsService): Injected LogsService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ResponsePointsConversion: The conversion details.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauthusers_id = None
    if token:
        token_data = await valid_access_token(token)
        oauthusers_id = token_data.data["sub"]
    try:
        add_log(
            "users",
            "INFO",
            "Convert points to coins",
            {"externalUserId": externalUserId, "schema": schema},
            service_log,
            api_key=api_key,
            oauth_user_id=oauthusers_id,
        )
        response = service.convert_points_to_coins_externalUserId(
            externalUserId, schema, api_key
        )
        return response
    except Exception as e:
        add_log(
            "users",
            "ERROR",
            "Convert points to coins failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauthusers_id,
        )
        raise e


summary_add_action_to_user = "Add Action to User"
description_add_action_to_user = """
## Add Action to User
### This endpoint adds an action to a specific user.
<sub>**Id_endpoint:** add_action_to_user</sub>
"""


@router.post(
    "/{externalUserId}/actions",
    response_model=CreatedUserActions,
    summary=summary_add_action_to_user,
    description=description_add_action_to_user,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def add_action_to_user(
    externalUserId: str,
    schema: CreateUserBodyActions,
    service: UserActionsService = Depends(Provide[Container.user_actions_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Add an action to a specific user.

    Args:
        externalUserId (str): The external user ID.
        schema (PostPointsConversionRequest): The schema containing action
          details.
        service (UserService): Injected UserService dependency.
        service_log (LogsService): Injected LogsService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ResponsePointsConversion: The action details.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauthusers_id = None
    if token:
        token_data = await valid_access_token(token)
        oauthusers_id = token_data.data["sub"]
    try:
        add_log(
            "users",
            "INFO",
            "Add action to user",
            {"externalUserId": externalUserId, "schema": schema},
            service_log,
            api_key=api_key,
            oauth_user_id=oauthusers_id,
        )
        response = service.user_add_action_default(externalUserId, schema, api_key)
        return response
    except Exception as e:
        add_log(
            "users",
            "ERROR",
            "Add action to user failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauthusers_id,
        )
        raise e
