

from app.model.base_model import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB


class UserPoints(BaseModel, table=True):
    points: int = Field(sa_column=Column(Integer))
    # data: is a json object
    data: dict = Field(sa_column=Column(JSONB), nullable=True)
    userId: int = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("users.id")))
    taskId: int = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("tasks.id")))

    def __str__(self):
        return f"UserPoints: {self.points}, {self.data}, {self.userId}, {self.taskId}"

    def __repr__(self):
        return f"UserPoints: {self.points}, {self.data}, {self.userId}, {self.taskId}"

    def __eq__(self, other):
        return (
            self.points == other.points and
            self.data == other.data and
            self.userId == other.userId and
            self.taskId == other.taskId
        )

    def __hash__(self):
        return hash((self.points, self.data, self.userId, self.taskId))

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.taskId < other.taskId

    def __le__(self, other):
        return self.taskId <= other.taskId

    def __gt__(self, other):
        return self.taskId > other.taskId

    def __ge__(self, other):
        return self.taskId >= other.taskId

    def __bool__(self):
        return self.taskId is not None
