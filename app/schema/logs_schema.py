from typing import Optional

from pydantic import BaseModel


class LogsBase(BaseModel):
    """
    Base model for logs

    """

    log_level: str
    message: str
    module: str
    details: dict
    apiKey_used: Optional[str]
    oauth_user_id: Optional[str]


class CreateLogs(LogsBase):
    """
    Model for creating a log

    """

    pass
