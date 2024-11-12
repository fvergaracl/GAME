from pydantic import BaseModel
from typing import List


class DashboardBase(BaseModel):
    """
    Base model for a dashboard
    """

    pass


# [{'label': datetime.datetime(2024, 10, 31, 0, 0, tzinfo=datetime.timezone.utc), 'count': 1}, {'label': datetime.datetime(2024, 10, 29, 0, 0, tzinfo=datetime.timezone.utc), 'count': 7}]


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
