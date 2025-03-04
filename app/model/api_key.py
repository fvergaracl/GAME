from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, DateTime, Field, ForeignKey, SQLModel, String, func


class ApiKey(SQLModel, table=True):
    """
    Represents an API key.

    Attributes:
        key (str): The API key.
        description (str) (optional): A description of the API key.
        active (bool): A flag indicating whether the API key is active.
        createdBy (str): The ID (userId Keycloak) of the user who created
          the API key. This is used to track the creator of the key.
    """

    # Field definitions
    id: str = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
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
    apiKey: str = Field(sa_column=Column(String, unique=True))
    client: str = Field(sa_column=Column(String))
    description: str = Field(sa_column=Column(String), nullable=True)
    active: bool = Field(sa_column=Column(Boolean), default=True)
    createdBy: str = Field(sa_column=Column(String))
    oauth_user_id: str = Field(
        sa_column=Column(
            String, ForeignKey("oauthusers.provider_user_id"), nullable=True
        )
    )

    class Config:
        orm_mode = True

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
            f"updated_at={self.updated_at}, apiKey={self.apikey}, "
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
