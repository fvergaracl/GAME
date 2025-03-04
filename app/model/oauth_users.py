from datetime import datetime
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, DateTime, Field, ForeignKey, SQLModel, String, func


class OAuthUsers(SQLModel, table=True):
    """
    Represents a user authenticated via OAuth.

    Attributes:
        provider (str): The OAuth provider.
        provider_user_id (str): The OAuth user ID.
        status (str): The status of the user (e.g., 'active', 'inactive').

    Methods:
        __str__: Return a string representation of the object.
        __repr__: Return a string representation of the object.
        __eq__: Compare if two objects are equal.
        __hash__: Return the hash of the object.

    """

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

    provider: str = Field(sa_column=Column(String))
    provider_user_id: str = Field(sa_column=Column(String, unique=True))
    status: str = Field(sa_column=Column(String), nullable=True)
    apiKey_used: str = Field(
        sa_column=Column(String, ForeignKey("apikey.apiKey"), nullable=True)
    )

    class Config:  # noqa
        orm_mode = True  # noqa

    def __str__(self):
        return (
            f"OAuthUsers: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, provider={self.provider}, "
            f"provider_user_id={self.provider_user_id}, status={self.status})"
        )

    def __repr__(self):
        return (
            f"OAuthUsers: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, provider={self.provider}, "
            f"provider_user_id={self.provider_user_id}, status={self.status})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, OAuthUsers)
            and self.provider == other.provider
            and self.provider_user_id == other.provider_user_id
            and self.status == other.status
        )

    def __hash__(self):
        return hash((self.provider, self.provider_user_id, self.status))
