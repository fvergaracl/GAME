from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlmodel import Column, Field, ForeignKey, String

from app.model.base_model import BaseModel


class UserActions(BaseModel, table=True):
    """
    Represents actions performed by a user. (Could be used for auditing
      purposes or for assigning points to a user.

    Attributes:
        typeAction (str): The type of action performed by the user.
        data (dict): A JSON object containing additional data.
        description (str): A description of the user action.
        userId (str): The ID of the user associated with the action.
    """

    typeAction: str = Field(sa_column=Column(String), nullable=True)
    data: dict = Field(sa_column=Column(JSONB), nullable=True)
    description: str = Field(sa_column=Column(String), nullable=True)
    userId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("users.id")))
    apiKey_used: str = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey(
            "apikey.apiKey"), nullable=True)
    )

    class Config:  # noqa
        orm_mode = True  # noqa

    def __str__(self):
        return (
            f"UserActions (id={self.id}, created_at={self.created_at},"
            f" updated_at={self.updated_at}, typeAction={self.typeAction}, "
            f"data={self.data}, description={self.description}, "
            f"userId={self.userId})"
        )

    def __repr__(self):
        return (
            f"UserActions (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, typeAction={self.typeAction}, "
            f"data={self.data}, description={self.description}, "
            f"userId={self.userId})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, UserActions)
            and self.id == other.id
            and self.typeAction == other.typeAction
            and self.data == other.data
            and self.description == other.description
            and self.userId == other.userId
        )

    def make_hashable(self, obj):
        if isinstance(obj, (tuple, list)):
            return tuple(self.make_hashable(e) for e in obj)
        elif isinstance(obj, dict):
            return tuple(sorted(
                (k, self.make_hashable(v)) for k, v in obj.items()))
        else:
            return obj

    def __hash__(self):
        data_as_hashable = self.make_hashable(self.data)
        return hash((
            self.typeAction, data_as_hashable, self.description, self.userId
        ))
