from sqlmodel import Column, Field, ForeignKey, String

from app.model.base_model import BaseModel
from pydantic import ConfigDict


class Users(BaseModel, table=True):
    """
    Represents a user in the application.

    Attributes:
        externalUserId (str): The external user ID.

    """

    externalUserId: str = Field(sa_column=Column(String, unique=True))
    apiKey_used: str = Field(
        sa_column=Column(String, ForeignKey("apikey.apiKey"), nullable=True)
    )

    model_config = ConfigDict(from_attributes=True)

    def __str__(self):
        return (
            f"User: (id:{self.id}, created_at:{self.created_at}, "
            f"updated_at:{self.updated_at}, "
            f"externalUserId:{self.externalUserId})"
        )

    def __repr__(self):
        return (
            f"User: (id:{self.id}, created_at:{self.created_at}, "
            f"updated_at:{self.updated_at}, "
            f"externalUserId:{self.externalUserId})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, Users)
            and self.id == other.id
            and self.externalUserId == other.externalUserId
        )

    def __hash__(self):
        return hash((self.id, self.externalUserId))
