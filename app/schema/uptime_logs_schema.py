from pydantic import BaseModel


class UptimeLogsBase(BaseModel):
    """
    Base model for Uptime Logs
    """

    status: str
