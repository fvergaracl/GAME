from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, Field, ForeignKey, String
from app.model.base_model import BaseModel


class TasksParams(BaseModel, table=True):
    """
    Represents the parameters for a task.

    Attributes:
        key (str): The key of the parameter.
        value (str): The value of the parameter.
        taskId (str): The ID of the task associated with the parameter.
    """

    key: str = Field(sa_column=Column(String))
    value: str = Field(sa_column=Column(String))
    taskId: str = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("tasks.id")))

    class Config:
        orm_mode = True

    def __str__(self):
        return f"TasksParams: (id={self.id}, created_at={self.created_at}, updated_at={self.updated_at}, key={self.key}, value={self.value}, taskId={self.taskId})"

    def __repr__(self):
        return f"TasksParams: (id={self.id}, created_at={self.created_at}, updated_at={self.updated_at}, key={self.key}, value={self.value}, taskId={self.taskId})"

    def __eq__(self, other):
        return (
            isinstance(other, TasksParams)
            and self.key == other.key
            and self.value == other.value
            and self.taskId == other.taskId
        )

    def __hash__(self):
        return hash((self.key, self.value, self.taskId))
