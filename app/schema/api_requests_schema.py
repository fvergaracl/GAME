from pydantic import BaseModel


class ApiRequestBase(BaseModel):
    """
    Base model for ApiRequest
    """

    userId: str
    endpoint: str
    statusCode: int
    responseTimeMS: int
    requestType: str
