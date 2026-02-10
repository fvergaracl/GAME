from pydantic import BaseModel, Field


class UptimeLogsBase(BaseModel):
    """
    Base schema for service uptime/health log entries.

    Attributes:
        status (str): Health status label reported by the uptime monitor.
          Typical values include `up`, `degraded`, or `down`.
    """

    status: str = Field(
        ...,
        description="Health status value emitted by uptime checks.",
        example="up",
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative payload for uptime logging.
        """
        return {"status": "up"}
