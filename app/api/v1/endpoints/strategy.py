import io
from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.container import Container
from app.core.exceptions import NotFoundError
from app.middlewares.valid_access_token import oauth_2_scheme, valid_access_token
from app.schema.oauth_users_schema import CreateOAuthUser
from app.schema.strategy_schema import Strategy
from app.services.apikey_service import ApiKeyService
from app.services.logs_service import LogsService
from app.services.oauth_users_service import OAuthUsersService
from app.services.strategy_service import StrategyService
from app.util.add_log import add_log

router = APIRouter(
    prefix="/strategies",
    tags=["strategies"],
)

summary_get_strategies_list = "Retrieve Strategies List"
description_get_strategies_list = """
## Retrieve Strategies List
### This endpoint retrieves a list of all available strategies.
<sub>**Id_endpoint:** get_strategy_list</sub>"""


@router.get(
    "",
    response_model=List[Strategy],
    summary=summary_get_strategies_list,
    description=description_get_strategies_list,
)
@inject
async def get_strategy_list(
    service: StrategyService = Depends(Provide[Container.strategy_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve a list of all strategies.

    Args:
        service (StrategyService): Injected StrategyService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[Strategy]: The list of all strategies.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "strategies",
                "INFO",
                "Get all strategies - User created",
                {
                    "oauth_user_id": oauth_user_id,
                },
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
    await add_log(
        "strategies",
        "INFO",
        "Get all strategies",
        {},
        service_log,
        api_key=api_key,
        oauth_user_id=oauth_user_id,
    )
    try:
        response = service.list_all_strategies()
        return response
    except Exception as e:
        await add_log(
            "strategies",
            "ERROR",
            "Get all strategies failed",
            {"error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise e


summary_get_strategy_by_id = "Retrieve Strategy by ID"
description_get_strategy_by_id = """
## Retrieve Strategy by ID
### This endpoint retrieves the details of a strategy using its unique ID. 
<sub>**Id_endpoint:** get_strategy_by_id</sub>"""


@router.get(
    "/{id}",
    response_model=Strategy,
    summary=summary_get_strategy_by_id,
    description=description_get_strategy_by_id,
)
@inject
async def get_strategy_by_id(
    id: str,
    service: StrategyService = Depends(Provide[Container.strategy_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve a strategy by its ID.

    Args:
        id (str): The ID of the strategy.
        service (StrategyService): Injected StrategyService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        Strategy: The details of the specified strategy.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "strategies",
                "INFO",
                "Get strategy by ID - User created",
                {
                    "oauth_user_id": oauth_user_id,
                },
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
    await add_log(
        "strategies",
        "INFO",
        "Get strategy by ID",
        {"id": id},
        service_log,
        api_key=api_key,
        oauth_user_id=oauth_user_id,
    )
    all_strategies = service.list_all_strategies()
    try:
        for strategy in all_strategies:
            if strategy["id"] == id:
                return strategy
        raise NotFoundError(detail=f"Strategy not found with id: {id}")
    except Exception as e:
        await add_log(
            "strategies",
            "ERROR",
            "Get strategy by ID failed",
            {"id": id, "error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise e


summary_get_strategy_graph_by_id = "Retrieve Strategy Graph by ID"
description_get_strategy_graph_by_id = """
## Retrieve Strategy Graph by ID
### This endpoint retrieves the logic graph of a strategy using its unique ID.
<sub>**Id_endpoint:** get_strategy_graph_by_id</sub>"""


@router.get(
    "/{id}/graph",
    summary=summary_get_strategy_graph_by_id,
    description=description_get_strategy_graph_by_id,
)
@inject
async def get_strategy_graph_by_id(
    id: str,
    service: StrategyService = Depends(Provide[Container.strategy_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve a strategy graph by its ID.

    Args:
        id (str): The ID of the strategy.
        service (StrategyService): Injected StrategyService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        StreamingResponse: The logic graph of the specified strategy.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "strategies",
                "INFO",
                "Get strategy graph by ID - User created",
                {
                    "oauth_user_id": oauth_user_id,
                },
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )
    try:
        await add_log(
            "strategies",
            "INFO",
            "Get strategy graph by ID",
            {"id": id},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        strategy = service.get_strategy_by_id(id)
        if not strategy:
            raise NotFoundError(detail=f"Strategy not found with id: {id}")
        strategy_class = service.get_Class_by_id(id)
        if strategy_class is None:
            raise NotFoundError(detail=f"No class found for strategy with id: {id}")
        dot = strategy_class.generate_logic_graph(format="png")

        graph_png = dot.pipe(format="png")

        return StreamingResponse(io.BytesIO(graph_png), media_type="image/png")
    except Exception as e:
        await add_log(
            "strategies",
            "ERROR",
            "Get strategy graph by ID failed",
            {"id": id, "error": str(e)},
            service_log,
            api_key=api_key,
            oauth_user_id=oauth_user_id,
        )
        raise e
