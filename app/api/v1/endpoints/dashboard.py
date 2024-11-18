from fastapi import APIRouter, Depends, Query
from app.middlewares.authentication import auth_api_key_or_oauth2
from app.schema.dashboard_schema import DashboardSummary
from app.services.dashboard_service import DashboardService
from app.services.apikey_service import ApiKeyService
from app.services.logs_service import LogsService
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
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        DashboardSummary: The dashboard summary.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauthusers_id = None
    if token:
        token_data = await valid_access_token(token)
        oauthusers_id = token_data.data["sub"]

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
        oauthusers_id,
    )

    return DashboardSummary(
        new_users=response.get("new_users", []),
        games_opened=response.get("games_opened", []),
        points_earned=response.get("points_earned", []),
        actions_performed=response.get("actions_performed", []),
    )
