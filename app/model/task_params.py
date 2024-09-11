from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, Field, ForeignKey, String

from app.model.base_model import BaseModel


class TasksParams(BaseModel, table=True):
    """
    Represents the parameters for a task, extending the functionality of the
      BaseModel with task-specific fields.

    Attributes:
        key (str): The key name of the parameter, acting as a descriptive
          identifier.
        value (str): The actual value of the parameter.
        taskId (str): The unique identifier of the task associated with this
         parameter, serves as a foreign key linking to the `tasks` table.

    Methods:
        __str__(self): Returns a human-readable string representation of the
          task parameter instance.
        __repr__(self): Returns a more formal string representation suitable
          for debugging.
        __eq__(self, other): Checks equality based on the task parameter's
          key, value, and associated task ID.
        __hash__(self): Generates a hash based on the key, value, and task ID,
          suitable for use in hash-based collections.

    Configurations:
        orm_mode (bool): Enables ORM compatibility mode, facilitating
          integration with database ORM frameworks.
    """

    key: str = Field(sa_column=Column(String))
    value: str = Field(sa_column=Column(String))
    taskId: str = Field(sa_column=Column(UUID(as_uuid=True), ForeignKey("tasks.id")))
    apiKey_used: str = Field(
        sa_column=Column(String, ForeignKey("apikey.apiKey"), nullable=True)
    )

    class Config:
        orm_mode = True

    def __str__(self):
        return (
            f"TasksParams: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, key={self.key}, "
            f"value={self.value}, taskId={self.taskId})"
        )

    def __repr__(self):
        return (
            f"TasksParams: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, key={self.key}, "
            f"value={self.value}, taskId={self.taskId})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, TasksParams)
            and self.key == other.key
            and self.value == other.value
            and self.taskId == other.taskId
        )

    def __hash__(self):
        return hash((self.key, self.value, self.taskId))
