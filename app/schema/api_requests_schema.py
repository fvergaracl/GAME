from pydantic import BaseModel


class ApiRequestBase(BaseModel):
    """
    Base model for ApiRequest
    """

    user_id: str
    endpoint: str
    status_code: int
    response_time_ms: int
    request_type: str
