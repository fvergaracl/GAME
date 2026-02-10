from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApikeyBase(BaseModel):
    """
    Base schema containing an API key value.

    Attributes:
        apiKey (str): Opaque API key token used to authorize requests.
    """

    apiKey: str = Field(
        ...,
        description="Opaque API key token used for API authentication.",
        example="gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
    )


class ApiKeyPostBody(BaseModel):
    """
    Request body schema for API key creation.

    Attributes:
        client (str): Consumer/client identifier that will own the API key.
        description (str): Human-readable description of the API key purpose.
    """

    client: str = Field(
        ...,
        description="Client identifier that will own the API key.",
        example="dashboard-service",
    )
    description: str = Field(
        ...,
        description="Human-readable purpose of this API key.",
        example="Read-only access for internal analytics dashboard",
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative payload for API key creation.
        """
        return {
            "client": "dashboard-service",
            "description": "Read-only access for internal analytics dashboard",
        }


class ApiKeyCreate(ApiKeyPostBody):
    """
    Internal schema used when creating an API key record.

    Attributes:
        createdBy (str): Identifier of the actor who created the key.
        apiKey (str): Generated API key value.
    """

    createdBy: str = Field(
        ...,
        description="Identifier of the user/system that created the key.",
        example="admin@game.local",
    )
    apiKey: str = Field(
        ...,
        description="Generated API key token.",
        example="gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
    )


class ApiKeyCreateBase(ApikeyBase):
    """
    Canonical API key resource representation.

    Attributes:
        apiKey (str): API key token.
        client (str): Client identifier that owns the key.
        description (str): Key purpose/usage description.
        createdBy (str): Actor that created the key.
    """

    apiKey: str = Field(
        ...,
        description="API key token.",
        example="gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
    )
    client: str = Field(
        ...,
        description="Client identifier associated with this API key.",
        example="dashboard-service",
    )
    description: str = Field(
        ...,
        description="Human-readable description of API key usage.",
        example="Read-only access for internal analytics dashboard",
    )
    createdBy: str = Field(
        ...,
        description="Identifier of the creator.",
        example="admin@game.local",
    )


class ApiKeyCreatedUnitList(ApiKeyCreateBase):
    """
    API key record returned as part of list responses.

    Attributes:
        created_at (datetime): UTC timestamp when the key was created.
    """

    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the API key was created.",
        example="2026-02-10T18:45:00Z",
    )


class ApiKeyCreated(ApiKeyCreateBase):
    """
    Response schema for API key creation operations.

    Attributes:
        message (Optional[str]): Operation result message.
    """

    message: Optional[str] = Field(
        default="Successfully created",
        description="Human-readable operation result message.",
        example="Successfully created",
    )
