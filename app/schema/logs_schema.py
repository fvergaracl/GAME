from pydantic import BaseModel


class LogsBase(BaseModel):
    """
    Base model for logs

    """

    log_level: str
    message: str
    module: str
    details: dict
    apiKey_used: str
    oauthusers_id: str
