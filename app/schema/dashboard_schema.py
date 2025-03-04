from typing import List

from pydantic import BaseModel


class DashboardBase(BaseModel):
    """
    Base model for a dashboard
    """

    pass


class DashboardSummaryElement(BaseModel):
    """
    Model for the dashboard summary element
    """

    label: str
    count: int | float


class DashboardSummary(BaseModel):
    """
    Model for the dashboard summary
    """

    # new_users is array of int
    new_users: List[DashboardSummaryElement]
    games_opened: List[DashboardSummaryElement]
    points_earned: List[DashboardSummaryElement]
    actions_performed: List[DashboardSummaryElement]


class DashboardSummaryLogs(BaseModel):
    """
    Model for the dashboard summary logs
    """

    info: List[DashboardSummaryElement]
    success: List[DashboardSummaryElement]
    error: List[DashboardSummaryElement]
