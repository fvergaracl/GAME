from pydantic import BaseModel, Field


class ApiRequestBase(BaseModel):
    """
    Canonical schema for API request telemetry records.

    This model captures request-level operational metrics so they can be
    persisted and aggregated for analytics, observability, and dashboard KPIs.

    Attributes:
        userId (str): Internal identifier of the actor that triggered the
          request.
        endpoint (str): API path pattern or route identifier that handled the
          request.
        statusCode (int): HTTP response status code returned by the endpoint.
        responseTimeMS (int): End-to-end response time in milliseconds.
        requestType (str): HTTP method of the request (for example: `GET`,
          `POST`, `PATCH`, `DELETE`).
    """

    userId: str = Field(
        ...,
        description="Internal user identifier associated with the request.",
        example="8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
    )
    endpoint: str = Field(
        ...,
        description="API endpoint path or route key processed by the server.",
        example="/api/v1/games/4ce32be2-77f6-4ffc-8e07-78dc220f0520/tasks",
    )
    statusCode: int = Field(
        ...,
        description="HTTP status code returned for the request.",
        example=200,
    )
    responseTimeMS: int = Field(
        ...,
        description="Request processing time in milliseconds.",
        example=84,
    )
    requestType: str = Field(
        ...,
        description="HTTP method of the request.",
        example="GET",
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative payload for API request telemetry ingestion.
        """
        return {
            "userId": "8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
            "endpoint": "/api/v1/games/4ce32be2-77f6-4ffc-8e07-78dc220f0520/tasks",
            "statusCode": 200,
            "responseTimeMS": 84,
            "requestType": "GET",
        }
