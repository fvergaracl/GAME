from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Boolean
from sqlmodel import Column, DateTime, Field, String, func, SQLModel
from uuid import uuid4
from datetime import datetime


class ApiKey(SQLModel, table=True):
    # api_key allows access to the API for third parties
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
    apiKey: str = Field(
        sa_column=Column(UUID(as_uuid=True), unique=True)
    )
    client: str = Field(
        sa_column=Column(String)
    )
    description: str = Field(
        sa_column=Column(String), nullable=True
    )
    active: bool = Field(
        sa_column=Column(Boolean), default=True
    )
    createdBy: str = Field(
        sa_column=Column(String)
    )

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True  # Allow arbitrary types like UUID

    def __str__(self):
        return (
            f"ApiKey: (apiKey={self.apiKey}, description={self.description}, "
            f"active={self.active}, createdBy={self.createdBy})"
        )

    def __repr__(self):
        return (
            f"ApiKey: (apiKey={self.apiKey}, description={self.description}, "
            f"active={self.active}, createdBy={self.createdBy})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, ApiKey)
            and self.apiKey == other.apiKey
            and self.description == other.description
            and self.active == other.active
            and self.createdBy == other.createdBy
        )
