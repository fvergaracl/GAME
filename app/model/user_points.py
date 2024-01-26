

from app.model.base_model import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime


class UserPoints(BaseModel, table=True):
    points: int = Field(sa_column=Column(Integer))
    description: str = Field(sa_column=Column(String))
    timestamp: datetime = Field(sa_column=Column(DateTime))
    userId: int = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("users.id")))
    taskId: int = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("tasks.id")))

    def __str__(self):
        return f"UserPoints: {self.points}, {self.description}, {self.timestamp}, {self.userId}, {self.taskId}"

    def __repr__(self):
        return f"UserPoints: {self.points}, {self.description}, {self.timestamp}, {self.userId}, {self.taskId}"

    def __eq__(self, other):
        return self.points == other.points and self.description == other.description and self.timestamp == other.timestamp and self.userId == other.userId and self.taskId == other.taskId

    def __hash__(self):
        return hash((self.points, self.description, self.timestamp, self.userId, self.taskId))

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.taskId < other.taskId
