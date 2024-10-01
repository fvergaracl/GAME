from pydantic import BaseModel


class KpiMetricsBase(BaseModel):
    """
    Base model for KpiMetrics
    """

    day: str
    totalRequests: int
    successRate: float
    avgLatencyMS: float
    errorRate: float
    activeUsers: int
    retentionRate: float
    avgInteractionsPerUser: float
