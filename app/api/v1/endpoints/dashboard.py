from fastapi import APIRouter, Depends, Query
from app.middlewares.authentication import auth_api_key_or_oauth2
from app.schema.dashboard_schema import DashboardSummary, DashboardSummaryLogs
from app.services.dashboard_service import DashboardService
from app.services.apikey_service import ApiKeyService
from app.services.logs_service import LogsService
from app.services.oauth_users_service import OAuthUsersService
from app.schema.oauth_users_schema import CreateOAuthUser
from dependency_injector.wiring import Provide, inject
from app.core.container import Container
from app.middlewares.valid_access_token import oauth_2_scheme, valid_access_token
from app.util.add_log import add_log

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


summary_get_dashboard_summary = "Get dashboard summary"
description_get_dashboard_summary = """
## Get dashboard summary
### Get dashboard summary

This endpoint returns the summary of the dashboard as New Users, Games Opened,
 Points Earned, and Actions Performed. 
<sub>**Id_endpoint:** get_dashboard_summary</sub>
"""


@router.get(
    "/summary",
    summary=summary_get_dashboard_summary,
    description=description_get_dashboard_summary,
    response_model=DashboardSummary,
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
description_get_dashboard_summary_logs = """
## Get dashboard summary logs
### Get dashboard summary logs

This endpoint returns the logs of the dashboard summary as INFO, SUCESS, ERROR.
<sub>**Id_endpoint:** get_dashboard_summary_logs</sub>
"""


@router.get(
    "/summary/logs",
    summary=summary_get_dashboard_summary_logs,
    description=description_get_dashboard_summary_logs,
    response_model=DashboardSummaryLogs,
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
