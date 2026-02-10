from typing import Optional

from pydantic import BaseModel, Field


class LogsBase(BaseModel):
    """
    Base schema for application log events.

    This model captures structured log information emitted by services and
    endpoints for observability, auditing, and analytics.

    Attributes:
        log_level (str): Severity level of the log event
          (for example: `INFO`, `SUCCESS`, `ERROR`).
        message (str): Human-readable log message.
        module (str): Logical module/component that generated the log.
        details (dict): Structured JSON payload with contextual attributes.
        apiKey_used (Optional[str]): API key involved in the request context,
          when available.
        oauth_user_id (Optional[str]): OAuth subject involved in the request
          context, when available.
    """

    log_level: str = Field(
        ...,
        description="Severity level of the log event.",
        example="INFO",
    )
    message: str = Field(
        ...,
        description="Human-readable log message.",
        example="Get dashboard summary",
    )
    module: str = Field(
        ...,
        description="Module or bounded context that generated the log.",
        example="dashboard",
    )
    details: dict = Field(
        ...,
        description="Structured metadata associated with the event.",
        example={"group_by": "day", "start_date": "2026-02-01", "end_date": "2026-02-10"},
    )
    apiKey_used: Optional[str] = Field(
        default=None,
        description="API key used in the request context, if any.",
        example="gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
    )
    oauth_user_id: Optional[str] = Field(
        default=None,
        description="OAuth user subject associated with the request, if any.",
        example="3c95c2d7-1ce8-4ea0-b35f-6dfd19127f35",
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative structured log payload.
        """
        return {
            "log_level": "INFO",
            "message": "Get dashboard summary",
            "module": "dashboard",
            "details": {
                "group_by": "day",
                "start_date": "2026-02-01",
                "end_date": "2026-02-10",
            },
            "apiKey_used": "gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
            "oauth_user_id": "3c95c2d7-1ce8-4ea0-b35f-6dfd19127f35",
        }


class CreateLogs(LogsBase):
    """
    Request schema used to create a new structured log record.
    """

    pass
