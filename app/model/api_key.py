import os
from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import ConfigDict
from sqlalchemy import Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, DateTime, Field, ForeignKey, SQLModel, String, func

from app.util.generate_api_key import extract_prefix, hash_api_key


class ApiKey(SQLModel, table=True):
    """
    Represents an API key used for authenticating and authorizing access to
    the system.

    Plaintext keys are never persisted. Each row stores:
      * ``apiKey`` -- the public prefix (e.g. ``gme_live_abc12345``).
        Safe to log and referenced by ``apiKey_used`` FK columns across
        the schema.
      * ``apiKeyHash`` -- ``sha256(plaintext)`` hex digest, used to
        authenticate requests in O(1) without ever storing the secret.

    Attributes:
        apiKey (str): Public key prefix.
        apiKeyHash (str): sha256 hex digest of the key plaintext.
        description (str) (optional): A description of the API key.
        active (bool): Flag indicating whether the API key is active.
        createdBy (str): Keycloak userId of the creator.
    """

    id: str = Field(
        default_factory=uuid4,
        sa_column=Column(UUID(as_uuid=True), primary_key=True, index=True),
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), default=func.now(), onupdate=func.now()
        )
    )
    apiKey: str = Field(sa_column=Column(String, unique=True, index=True))
    apiKeyHash: str = Field(sa_column=Column(String, unique=True, index=True))
    client: str = Field(sa_column=Column(String))
    description: str = Field(sa_column=Column(String, nullable=True))
    active: bool = Field(sa_column=Column(Boolean, default=True))
    createdBy: str = Field(sa_column=Column(String))
    oauth_user_id: str = Field(
        sa_column=Column(
            String, ForeignKey("oauthusers.provider_user_id"), nullable=True
        )
    )

    model_config = ConfigDict(from_attributes=True)

    def __str__(self):
        return (
            f"ApiKey: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, apiKey={self.apiKey}, "
            f"description={self.description}, active={self.active}, "
            f"createdBy={self.createdBy})"
        )

    def __repr__(self):
        return (
            f"ApiKey: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, apiKey={self.apiKey}, "
            f"description={self.description}, active={self.active}, "
            f"createdBy={self.createdBy})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, ApiKey)
            and self.apiKey == other.apiKey
            and self.description == other.description
            and self.active == other.active
            and self.createdBy == other.createdBy
        )

    @staticmethod
    def get_e2e_seed_api_key() -> Optional[str]:
        """
        Returns the E2E seed API key plaintext from environment variable
        `E2E_API_KEY_GAME`, or None when missing/empty.
        """
        seed_value = os.getenv("E2E_API_KEY_GAME")
        if seed_value is None:
            return None
        normalized_seed = seed_value.strip()
        if not normalized_seed:
            return None
        return normalized_seed

    @classmethod
    def build_e2e_seed(
        cls,
        *,
        created_by: str,
        client: str = "e2e-seeded-client",
        description: str = "Seeded API key from E2E_API_KEY_GAME",
        oauth_user_id: Optional[str] = None,
    ) -> Optional["ApiKey"]:
        """
        Builds an ApiKey row from the plaintext stored in
        ``E2E_API_KEY_GAME``. The row only carries the derived prefix and
        hash; the plaintext is not persisted.

        Returns None when the env variable is not configured.
        """
        seed_plaintext = cls.get_e2e_seed_api_key()
        if seed_plaintext is None:
            return None

        return cls(
            apiKey=extract_prefix(seed_plaintext),
            apiKeyHash=hash_api_key(seed_plaintext),
            client=client,
            description=description,
            active=True,
            createdBy=created_by,
            oauth_user_id=oauth_user_id,
        )
