from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlmodel import Column, Field, ForeignKey, Integer, String

from app.model.base_model import BaseModel


class UserPoints(BaseModel, table=True):
    """
    Represents the points and associated data for a user.

    Attributes:
        points (int): The number of points.
        caseName (str): The name of the case.
        data (dict): A JSON object containing additional data.
        description (str): A description of the user points.
        userId (str): The ID of the user associated with the points.
        taskId (str): The ID of the task associated with the points.
    """

    points: int = Field(sa_column=Column(Integer))
    caseName: str = Field(sa_column=Column(String), nullable=True)
    data: dict = Field(sa_column=Column(JSONB), nullable=True)
    description: str = Field(sa_column=Column(String), nullable=True)
    userId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("users.id")))
    taskId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("tasks.id")))
    apiKey_used: str = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey(
            "apikey.apiKey"), nullable=True)
    )

    class Config:  # noqa
        orm_mode = True  # noqa

    def __str__(self):
        return (
            f"UserPoints (id={self.id}, created_at={self.created_at},"
            f" updated_at={self.updated_at}, points={self.points}, "
            f"caseName={self.caseName}, data={self.data}, "
            f"description={self.description}, userId={self.userId}, "
            f"taskId={self.taskId})"
        )

    def __repr__(self):
        return (
            f"UserPoints (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, points={self.points}, "
            f"caseName={self.caseName}, data={self.data}, "
            f"description={self.description}, userId={self.userId}, "
            f"taskId={self.taskId})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, UserPoints)
            and self.id == other.id
            and self.points == other.points
            and self.caseName == other.caseName
            and self.data == other.data
            and self.description == other.description
            and self.userId == other.userId
            and self.taskId == other.taskId
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
            self.points, self.caseName, data_as_hashable, self.description,
            self.userId, self.taskId))
