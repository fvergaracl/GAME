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
response_example_get_strategies_list = [
    {
        "id": "default",
        "name": "Default Strategy",
        "description": "Baseline adaptive scoring strategy.",
        "version": "1.0.0",
        "variables": {
            "variable_basic_points": 10,
            "bonus_multiplier": 1.2,
        },
        "hash_version": "9e6c5ce8f3fcb2a4f6b5b2f1c1d2a9f7",
    },
    {
        "id": "constantEffortStrategy",
        "name": "Constant Effort",
        "description": "Awards stable points for repeated behavior.",
        "version": "1.0.0",
        "variables": {
            "variable_basic_points": 5,
        },
        "hash_version": "f1a2c3d4e5f60987654321aabbccdde0",
    },
]

responses_get_strategies_list = {
    200: {
        "description": "Strategies retrieved successfully",
        "content": {
            "application/json": {"example": response_example_get_strategies_list}
        },
    },
    401: {
        "description": "Unauthorized: invalid bearer token when provided",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    500: {
        "description": "Internal server error while listing strategies",
    },
}

description_get_strategies_list = """
Returns all scoring strategies available in the engine.

### Authentication
- Supports `Authorization: Bearer <access_token>` and `X-API-Key`.
- Authentication is optional for read-only listing; when provided, user context is logged.

### Success (200)
Returns a list of strategies with:
- `id`
- `name`
- `description`
- `version`
- `variables`
- `hash_version`

### Error Cases
- `401`: invalid bearer token (when token is sent)
- `500`: strategy retrieval failure

<sub>**Id_endpoint:** `get_strategy_list`</sub>
"""  # noqa


@router.get(
    "",
    response_model=List[Strategy],
    summary=summary_get_strategies_list,
    description=description_get_strategies_list,
    responses=responses_get_strategies_list,
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
response_example_get_strategy_by_id = {
    "id": "default",
    "name": "Default Strategy",
    "description": "Baseline adaptive scoring strategy.",
    "version": "1.0.0",
    "variables": {
        "variable_basic_points": 10,
        "bonus_multiplier": 1.2,
    },
    "hash_version": "9e6c5ce8f3fcb2a4f6b5b2f1c1d2a9f7",
}

responses_get_strategy_by_id = {
    200: {
        "description": "Strategy retrieved successfully",
        "content": {"application/json": {"example": response_example_get_strategy_by_id}},
    },
    401: {
        "description": "Unauthorized: invalid bearer token when provided",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    404: {
        "description": "Strategy not found for the provided id",
        "content": {
            "application/json": {
                "example": {"detail": "Strategy not found with id: default-v2"}
            }
        },
    },
    500: {
        "description": "Internal server error while retrieving strategy",
    },
}

description_get_strategy_by_id = """
Returns one strategy by its identifier.

### Path Parameter
- `id` (`string`): Unique strategy id (for example: `default`, `constantEffortStrategy`).

### Authentication
- Supports `Authorization: Bearer <access_token>` and `X-API-Key`.
- Authentication is optional for read-only retrieval; when provided, user context is logged.

### Success (200)
Returns the strategy object with:
- `id`
- `name`
- `description`
- `version`
- `variables`
- `hash_version`

### Error Cases
- `401`: invalid bearer token (when token is sent)
- `404`: no strategy found with the provided `id`
- `500`: strategy retrieval failure

<sub>**Id_endpoint:** `get_strategy_by_id`</sub>
"""  # noqa


@router.get(
    "/{id}",
    response_model=Strategy,
    summary=summary_get_strategy_by_id,
    description=description_get_strategy_by_id,
    responses=responses_get_strategy_by_id,
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
responses_get_strategy_graph_by_id = {
    200: {
        "description": "Strategy logic graph rendered as PNG image",
        "content": {
            "image/png": {
                "schema": {
                    "type": "string",
                    "format": "binary",
                }
            }
        },
    },
    401: {
        "description": "Unauthorized: invalid bearer token when provided",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    404: {
        "description": "Strategy id not found or graph class unavailable",
        "content": {
            "application/json": {
                "example": {"detail": "Strategy not found with id: default-v2"}
            }
        },
    },
    500: {
        "description": "Internal server error while generating strategy graph",
    },
}

description_get_strategy_graph_by_id = """
Returns a visual representation of a strategy logic graph as a PNG image.

### Path Parameter
- `id` (`string`): Strategy identifier (for example: `default`).

### Authentication
- Supports `Authorization: Bearer <access_token>` and `X-API-Key`.
- Authentication is optional for read-only retrieval; when provided, user context is logged.

### Success (200)
- Content-Type: `image/png`
- Body: binary PNG payload with the generated strategy graph.

### Error Cases
- `401`: invalid bearer token (when token is sent)
- `404`: strategy not found or missing graph-capable class
- `500`: graph generation failure

<sub>**Id_endpoint:** `get_strategy_graph_by_id`</sub>
"""  # noqa


@router.get(
    "/{id}/graph",
    summary=summary_get_strategy_graph_by_id,
    description=description_get_strategy_graph_by_id,
    response_class=StreamingResponse,
    responses=responses_get_strategy_graph_by_id,
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
