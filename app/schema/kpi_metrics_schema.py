from pydantic import BaseModel, Field


class KpiMetricsBase(BaseModel):
    """
    Daily KPI aggregate schema for operational and engagement monitoring.

    Attributes:
        day (str): Reporting day label (typically ISO date).
        totalRequests (int): Total number of API requests processed.
        successRate (float): Percentage of successful requests.
        avgLatencyMS (float): Average request latency in milliseconds.
        errorRate (float): Percentage of failed requests.
        activeUsers (int): Number of distinct active users for the day.
        retentionRate (float): Retention percentage for the analyzed cohort/day.
        avgInteractionsPerUser (float): Average number of interactions per active user.
    """

    day: str = Field(
        ...,
        description="Reporting day (ISO date or bucket label).",
        example="2026-02-10",
    )
    totalRequests: int = Field(
        ...,
        description="Total number of requests received/processed during the day.",
        example=1520,
    )
    successRate: float = Field(
        ...,
        description="Successful request ratio expressed as percentage.",
        example=98.7,
    )
    avgLatencyMS: float = Field(
        ...,
        description="Average end-to-end request latency in milliseconds.",
        example=84.6,
    )
    errorRate: float = Field(
        ...,
        description="Failed request ratio expressed as percentage.",
        example=1.3,
    )
    activeUsers: int = Field(
        ...,
        description="Number of unique users with activity in the period.",
        example=245,
    )
    retentionRate: float = Field(
        ...,
        description="Retention rate percentage for the tracked cohort.",
        example=62.4,
    )
    avgInteractionsPerUser: float = Field(
        ...,
        description="Average number of interactions performed per active user.",
        example=6.8,
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative daily KPI metrics payload.
        """
        return {
            "day": "2026-02-10",
            "totalRequests": 1520,
            "successRate": 98.7,
            "avgLatencyMS": 84.6,
            "errorRate": 1.3,
            "activeUsers": 245,
            "retentionRate": 62.4,
            "avgInteractionsPerUser": 6.8,
        }
