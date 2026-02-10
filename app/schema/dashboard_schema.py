from typing import List

from pydantic import BaseModel, Field


class DashboardBase(BaseModel):
    """
    Base dashboard schema marker.

    Used as a common parent for dashboard-related response models.
    """

    pass


class DashboardSummaryElement(BaseModel):
    """
    Single metric datapoint in a dashboard time series.

    Attributes:
        label (str): Time bucket or grouping label (for example a date/week/month).
        count (int | float): Aggregated metric value for that label.
    """

    label: str = Field(
        ...,
        description="Time bucket or grouping label.",
        example="2026-02-10",
    )
    count: int | float = Field(
        ...,
        description="Aggregated metric value for the given label.",
        example=42,
    )


class DashboardSummary(BaseModel):
    """
    Aggregated dashboard KPI summary grouped by time buckets.

    Attributes:
        new_users (List[DashboardSummaryElement]): Number of newly created users.
        games_opened (List[DashboardSummaryElement]): Number of game sessions opened.
        points_earned (List[DashboardSummaryElement]): Total points awarded.
        actions_performed (List[DashboardSummaryElement]): Total user actions recorded.
    """

    new_users: List[DashboardSummaryElement] = Field(
        ...,
        description="Time-series of new users created.",
    )
    games_opened: List[DashboardSummaryElement] = Field(
        ...,
        description="Time-series of opened games.",
    )
    points_earned: List[DashboardSummaryElement] = Field(
        ...,
        description="Time-series of points awarded to users.",
    )
    actions_performed: List[DashboardSummaryElement] = Field(
        ...,
        description="Time-series of user actions performed.",
    )


class DashboardSummaryLogs(BaseModel):
    """
    Aggregated dashboard log counters by severity and time bucket.

    Attributes:
        info (List[DashboardSummaryElement]): Count of informational logs.
        success (List[DashboardSummaryElement]): Count of success logs.
        error (List[DashboardSummaryElement]): Count of error logs.
    """

    info: List[DashboardSummaryElement] = Field(
        ...,
        description="Time-series count of INFO logs.",
    )
    success: List[DashboardSummaryElement] = Field(
        ...,
        description="Time-series count of SUCCESS logs.",
    )
    error: List[DashboardSummaryElement] = Field(
        ...,
        description="Time-series count of ERROR logs.",
    )
