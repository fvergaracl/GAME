from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.core.container import Container
from app.middlewares.authentication import auth_api_key_or_oauth2
from app.middlewares.valid_access_token import oauth_2_scheme, valid_access_token
from app.schema.dashboard_schema import DashboardSummary, DashboardSummaryLogs
from app.schema.oauth_users_schema import CreateOAuthUser
from app.services.apikey_service import ApiKeyService
from app.services.dashboard_service import DashboardService
from app.services.logs_service import LogsService
from app.services.oauth_users_service import OAuthUsersService
from app.util.add_log import add_log

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


summary_get_dashboard_summary = "Get dashboard summary"
response_example_get_dashboard_summary = {
    "new_users": [
        {"label": "2026-02-08", "count": 5},
        {"label": "2026-02-09", "count": 7},
        {"label": "2026-02-10", "count": 4},
    ],
    "games_opened": [
        {"label": "2026-02-08", "count": 12},
        {"label": "2026-02-09", "count": 18},
        {"label": "2026-02-10", "count": 11},
    ],
    "points_earned": [
        {"label": "2026-02-08", "count": 940},
        {"label": "2026-02-09", "count": 1280},
        {"label": "2026-02-10", "count": 870},
    ],
    "actions_performed": [
        {"label": "2026-02-08", "count": 37},
        {"label": "2026-02-09", "count": 49},
        {"label": "2026-02-10", "count": 33},
    ],
}

responses_get_dashboard_summary = {
    200: {
        "description": "Dashboard summary retrieved successfully",
        "content": {
            "application/json": {"example": response_example_get_dashboard_summary}
        },
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    422: {
        "description": "Validation error in query parameters",
    },
    500: {
        "description": "Internal server error while retrieving dashboard summary",
    },
}

description_get_dashboard_summary = """
Returns aggregated KPI metrics for the dashboard within an optional date window.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Query Parameters
- `start_date` (`string`, optional): Start of the reporting range.
- `end_date` (`string`, optional): End of the reporting range.
- `group_by` (`string`, optional): Aggregation granularity (`day`, `week`, `month`).

### Success (200)
Returns time-series aggregates for:
- `new_users`
- `games_opened`
- `points_earned`
- `actions_performed`

Each series item contains:
- `label` (time bucket label)
- `count` (numeric aggregate)

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `422`: invalid query parameters
- `500`: summary calculation failure

<sub>**Id_endpoint:** `get_dashboard_summary`</sub>
"""


@router.get(
    "/summary",
    summary=summary_get_dashboard_summary,
    description=description_get_dashboard_summary,
    response_model=DashboardSummary,
    responses=responses_get_dashboard_summary,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_dashboard_summary(
    start_date: str = Query(None, description="Start date"),
    end_date: str = Query(None, description="End date"),
    group_by: str = Query(None, description="Group by (day, week, month)"),
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Get dashboard summary

    Args:
        start_date (str): Start date.
        end_date (str): End date.
        group_by (str): Group by (day, week, month).
        service (DashboardService): The dashboard service.
        service_log (LogsService): The logs service.
        service_oauth (OAuthUsersService): The OAuth users service.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        DashboardSummary: The dashboard summary.
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
                "api_key",
                "INFO",
                "Get dashboard summary - User created",
                {
                    "oauth_user_id": oauth_user_id,
                },
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )

    response = service.get_dashboard_summary(start_date, end_date, group_by)

    await add_log(
        "dashboard",
        "INFO",
        "Get dashboard summary",
        {
            "length_new_users": len(response.get("new_users", [])),
            "length_games_opened": len(response.get("games_opened", [])),
            "length_points_earned": len(response.get("points_earned", [])),
            "length_actions_performed": len(response.get("actions_performed", [])),
        },
        service_log,
        api_key,
        oauth_user_id,
    )

    return DashboardSummary(
        new_users=response.get("new_users", []),
        games_opened=response.get("games_opened", []),
        points_earned=response.get("points_earned", []),
        actions_performed=response.get("actions_performed", []),
    )


summary_get_dashboard_summary_logs = "Get dashboard summary logs"
response_example_get_dashboard_summary_logs = {
    "info": [
        {"label": "2026-02-08", "count": 124},
        {"label": "2026-02-09", "count": 137},
        {"label": "2026-02-10", "count": 118},
    ],
    "success": [
        {"label": "2026-02-08", "count": 96},
        {"label": "2026-02-09", "count": 112},
        {"label": "2026-02-10", "count": 91},
    ],
    "error": [
        {"label": "2026-02-08", "count": 3},
        {"label": "2026-02-09", "count": 5},
        {"label": "2026-02-10", "count": 2},
    ],
}

responses_get_dashboard_summary_logs = {
    200: {
        "description": "Dashboard summary logs retrieved successfully",
        "content": {
            "application/json": {"example": response_example_get_dashboard_summary_logs}
        },
    },
    401: {
        "description": "Unauthorized: missing/invalid credentials",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    403: {
        "description": "Forbidden: invalid or inactive API key",
        "content": {
            "application/json": {
                "example": {"detail": "API key is invalid or does not exist."}
            }
        },
    },
    422: {
        "description": "Validation error in query parameters",
    },
    500: {
        "description": "Internal server error while retrieving dashboard summary logs",
    },
}

description_get_dashboard_summary_logs = """
Returns aggregated dashboard log counters grouped by severity within an optional date window.

### Authentication
- Requires either `X-API-Key` or `Authorization: Bearer <access_token>`.

### Query Parameters
- `start_date` (`string`, optional): Start of the reporting range.
- `end_date` (`string`, optional): End of the reporting range.
- `group_by` (`string`, optional): Aggregation granularity (`day`, `week`, `month`).

### Success (200)
Returns time-series aggregates for:
- `info`
- `success`
- `error`

Each series item contains:
- `label` (time bucket label)
- `count` (numeric aggregate)

### Error Cases
- `401`: missing or invalid auth credentials
- `403`: API key rejected or inactive
- `422`: invalid query parameters
- `500`: summary-log calculation failure

<sub>**Id_endpoint:** `get_dashboard_summary_logs`</sub>
"""


@router.get(
    "/summary/logs",
    summary=summary_get_dashboard_summary_logs,
    description=description_get_dashboard_summary_logs,
    response_model=DashboardSummaryLogs,
    responses=responses_get_dashboard_summary_logs,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_dashboard_summary_logs(
    start_date: str = Query(None, description="Start date"),
    end_date: str = Query(None, description="End date"),
    group_by: str = Query(None, description="Group by (day, week, month)"),
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Get dashboard summary logs , group by (day, week, month) and start_date and end_date

    Args:
        start_date (str): Start date.
        end_date (str): End date.
        group_by (str): Group by (day, week, month).
        service (DashboardService): The dashboard service.
        service_log (LogsService): The logs service.
        service_oauth (OAuthUsersService): The OAuth users service.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        DashboardSummaryLogs: The dashboard summary logs.
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
                "api_key",
                "INFO",
                "Get dashboard summary logs - User created",
                {
                    "oauth_user_id": oauth_user_id,
                },
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )

    response = service.get_dashboard_summary_logs(start_date, end_date, group_by)
    await add_log(
        "dashboard",
        "INFO",
        "Get dashboard summary logs",
        {
            "length_info": len(response.get("info", [])),
            "length_success": len(response.get("success", [])),
            "length_error": len(response.get("error", [])),
        },
        service_log,
        api_key,
        oauth_user_id,
    )

    return DashboardSummaryLogs(
        info=response.get("info", []),
        success=response.get("success", []),
        error=response.get("error", []),
    )


# # get_dashboard_summary_logs_module_counts
# summary_get_dashboard_summary_logs_module_counts = (
#     "Get dashboard summary logs module counts"
# )
# description_get_dashboard_summary_logs_module_counts = """
# ## Get dashboard summary logs module counts
# ### Get dashboard summary logs module counts

# This endpoint returns the logs of the dashboard summary as INFO, SUCESS, ERROR.
# <sub>**Id_endpoint:** get_dashboard_summary_logs_module_counts</sub>
# """


# @router.get(
#     "/summary/logs/module_counts",
#     summary=summary_get_dashboard_summary_logs_module_counts,
#     description=description_get_dashboard_summary_logs_module_counts,
#     response_model=DashboardSummaryLogs,
#     dependencies=[Depends(auth_api_key_or_oauth2)],
# )
# @inject
# async def get_dashboard_summary_logs_module_counts(
#     start_date: str = Query(None, description="Start date"),
#     end_date: str = Query(None, description="End date"),
#     group_by: str = Query(None, description="Group by (day, week, month)"),
#     service: DashboardService = Depends(Provide[Container.dashboard_service]),
#     service_log: LogsService = Depends(Provide[Container.logs_service]),
#     service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
#     token: str = Depends(oauth_2_scheme),
#     api_key_header: str = Depends(ApiKeyService.get_api_key_header),
# ):
#     """
#     Get dashboard summary logs module counts , group by (day, week, month) and start_date and end_date

#     Args:
#         start_date (str): Start date.
#         end_date (str): End date.
#         group_by (str): Group by (day, week, month).
#         service (DashboardService): The dashboard service.
#         service_log (LogsService): The logs service.
#         service_oauth (OAuthUsersService): The OAuth users service.
#         token (str): The OAuth2 token.
#         api_key_header (str): The API key header.

#     Returns:
#         DashboardSummaryLogs: The dashboard summary logs.
#     """
#     api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
#     oauth_user_id = None
#     if token:
#         token_data = await valid_access_token(token)
#         oauth_user_id = token_data.data["sub"]
#         if service_oauth.get_user_by_sub(oauth_user_id) is None:
#             create_user = CreateOAuthUser(
#                 provider="keycloak",
#                 provider_user_id=oauth_user_id,
#                 status="active",
#             )
#             await service_oauth.add(create_user)
#             await add_log(
#                 "api_key",
#                 "INFO",
#                 "Get dashboard summary logs module counts - User created",
#                 {
#                     "oauth_user_id": oauth_user_id,
#                 },
#                 service_log,
#                 api_key=api_key,
#                 oauth_user_id=oauth_user_id,
#             )

#     response = service.get_dashboard_summary_logs_module_counts(
#         start_date, end_date, group_by
#     )
#     await add_log(
#         "dashboard",
#         "INFO",
#         "Get dashboard summary logs module counts",
#         {
#             "length_info": len(response.get("info", [])),
#             "length_success": len(response.get("success", [])),
#             "length_error": len(response.get("error", [])),
#         },
#         service_log,
#         api_key,
#         oauth_user_id,
#     )

#     return DashboardSummaryLogs(
#         info=response.get("info", []),
#         success=response.get("success", []),
#         error=response.get("error", []),
#     )
