from fastapi import APIRouter, Depends, Query
from app.middlewares.authentication import auth_api_key_or_oauth2
from app.schema.dashboard_schema import DashboardSummary
from app.services.dashboard_service import DashboardService
from dependency_injector.wiring import Provide, inject
from app.core.container import Container

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


summary_get_dashboard_summary = "Get dashboard summary"
description_get_dashboard_summary = """
## Get dashboard summary
### Get dashboard summary

This endpoint returns the summary of the dashboard as New Users, Games Opened, Points Earned, and Actions Performed. 
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
def get_dashboard_summary(
    start_date: str = Query(None, description="Start date"),
    end_date: str = Query(None, description="End date"),
    group_by: str = Query(None, description="Group by (day, week, month)"),
    service: DashboardService = Depends(Provide[Container.dashboard_service]),
):
    """
    Get dashboard summary
    """

    response = service.get_dashboard_summary(start_date, end_date, group_by)
    return DashboardSummary(
        new_users=response.get("new_users", []),
        games_opened=response.get("games_opened", []),
        points_earned=response.get("points_earned", []),
        actions_performed=response.get("actions_performed", [])
    )
