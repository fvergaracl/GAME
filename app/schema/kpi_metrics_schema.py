from pydantic import BaseModel


class KpiMetricsBase(BaseModel):
    """
    Base model for KpiMetrics
    """

    day: str
    total_requests: int
    success_rate: float
    avg_latency_ms: float
    error_rate: float
    active_users: int
    retention_rate: float
    avg_interactions_per_user: float
