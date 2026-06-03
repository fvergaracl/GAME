from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApikeyBase(BaseModel):
    """
    Base schema containing the public API key prefix.

    Attributes:
        apiKey (str): Public key prefix (``gme_live_<8chars>``). Safe to log.
    """

    apiKey: str = Field(
        ...,
        description="Public API key prefix (safe to log/audit).",
        examples=["gme_live_3f6a9e0f"],
    )


class ApiKeyPostBody(BaseModel):
    """
    Request body schema for API key creation.

    Attributes:
        client (str): Consumer/client identifier that will own the key.
        description (str): Human-readable description of the key purpose.
    """

    client: str = Field(
        ...,
        description="Client identifier that will own the API key.",
        examples=["dashboard-service"],
    )
    description: str = Field(
        ...,
        description="Human-readable purpose of this API key.",
        examples=["Read-only access for internal analytics dashboard"],
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
    Internal schema used when persisting an API key record. Never carries
    the plaintext: only the public prefix and the canonical sha256 hash.

    Attributes:
        createdBy (str): Identifier of the actor who created the key.
        apiKey (str): Public prefix persisted in the DB.
        apiKeyHash (str): sha256(plaintext) used as the auth lookup key.
    """

    createdBy: str = Field(
        ...,
        description="Identifier of the user/system that created the key.",
        examples=["admin@game.local"],
    )
    apiKey: str = Field(
        ...,
        description="Public prefix persisted in the DB.",
        examples=["gme_live_3f6a9e0f"],
    )
    apiKeyHash: str = Field(
        ...,
        description="sha256(plaintext) hex digest used for auth lookups.",
        examples=["0c3a8d9b...e6f4"],
    )


class ApiKeyCreateBase(ApikeyBase):
    """
    Canonical API key resource representation (no plaintext, no hash).

    Attributes:
        apiKey (str): Public prefix.
        client (str): Client identifier that owns the key.
        description (str): Key purpose/usage description.
        createdBy (str): Actor that created the key.
    """

    apiKey: str = Field(
        ...,
        description="Public API key prefix.",
        examples=["gme_live_3f6a9e0f"],
    )
    client: str = Field(
        ...,
        description="Client identifier associated with this API key.",
        examples=["dashboard-service"],
    )
    description: Optional[str] = Field(
        None,
        description="Human-readable description of API key usage.",
        examples=["Read-only access for internal analytics dashboard"],
    )
    createdBy: str = Field(
        ...,
        description="Identifier of the creator.",
        examples=["admin@game.local"],
    )


class ApiKeyCreatedUnitList(ApiKeyCreateBase):
    """
    API key record returned as part of list responses.

    Attributes:
        created_at (datetime): UTC timestamp when the key was created.
        active (bool): Whether the key is still usable.
    """

    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the API key was created.",
        examples=["2026-02-10T18:45:00Z"],
    )
    active: Optional[bool] = Field(
        True,
        description="Whether this API key is currently active.",
        examples=[True],
    )


class ApiKeyCreated(ApiKeyCreateBase):
    """
    Response schema for API key creation. The plaintext is exposed here
    exactly once; subsequent endpoints will only ever return ``apiKey``
    (the public prefix).

    Attributes:
        plaintext (str): Full key value shown to the caller exactly once.
        apiKey (str): Public prefix; will continue to be visible after this
            response (e.g. in the listing endpoint).
        message (Optional[str]): Operation result message.
    """

    plaintext: str = Field(
        ...,
        description=(
            "Full API key value. Returned **only** at creation time; the "
            "server does not store it and cannot retrieve it again."
        ),
        examples=["gme_live_3f6a9e0f.AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEf"],
    )
    message: Optional[str] = Field(
        default="Successfully created",
        description="Human-readable operation result message.",
        examples=["Successfully created"],
    )


class ApiKeyRevoked(BaseModel):
    """
    Response schema returned by the revoke endpoint.
    """

    apiKey: str = Field(
        ...,
        description="Public prefix of the revoked key.",
        examples=["gme_live_3f6a9e0f"],
    )
    active: bool = Field(
        False,
        description="Whether the key is active after revocation.",
        examples=[False],
    )
    message: str = Field(
        "API key revoked successfully.",
        description="Human-readable operation result message.",
        examples=["API key revoked successfully."],
    )
