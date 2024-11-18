from sqlmodel import Column, Field, String

from app.model.base_model import BaseModel


class OAuthUsers(BaseModel, table=True):
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

    provider: str = Field(sa_column=Column(String))
    provider_user_id: str = Field(sa_column=Column(String))
    status: str = Field(sa_column=Column(String), nullable=True)

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
