from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, Field, ForeignKey, String

from app.model.base_model import BaseModel


class Tasks(BaseModel, table=True):
    """
    Defines the `Tasks` table for managing tasks associated with games in a
      SQL database.

    This model represents a task entity within a gaming context, uniquely
      identified by an external ID.
    Each task is linked to a specific game by its ID and can be optionally
      associated with a predefined strategy.

    Attributes:
        externalTaskId (str): A unique identifier for the task, sourced
          externally, ensuring each task can be distinctly referenced outside
            the system.
        gameId (UUID): The UUID of the game this task is associated with,
          creating a foreign key relationship to the `games` table.
        strategyId (str): The identifier for the strategy linked to this task,
          which defaults to 'default' if not explicitly provided. This field
            is not nullable, ensuring every task has a strategy associated.

    Configurations:
        orm_mode (bool): Enables ORM compatibility mode, allowing the model
          to be used with ORM frameworks seamlessly.

    Methods:
        __str__(self): Returns a human-readable string representation of the
          task, useful for logging and debugging.
        __repr__(self): Provides a formal representation of the task,
          identical to __str__ for consistency.
        __eq__(self, other): Compares this task with another for equality,
          considering all key attributes.
        __hash__(self): Computes a hash based on the task's ID, external ID,
          game ID, and strategy ID for use in hash-based collections.
    """

    externalTaskId: str = Field(sa_column=Column(String, nullable=False))
    gameId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("games.id")))
    strategyId: str = Field(sa_column=Column(
        String, nullable=False, default="default"))
    status: str = Field(sa_column=Column(
        String, nullable=False, default="open"))
    apiKey_used: str = Field(
        sa_column=Column(String, ForeignKey("apikey.apiKey"), nullable=True)
    )

    class Config:
        orm_mode = True  # Enable ORM mode

    def __str__(self):
        return (
            f"Tasks(id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, "
            f"externalTaskId={self.externalTaskId}, gameId={self.gameId}, "
            f"strategyId={self.strategyId}, status={self.status})"
        )

    def __repr__(self):
        return (
            f"Tasks(id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, "
            f"externalTaskId={self.externalTaskId}, gameId={self.gameId}, "
            f"strategyId={self.strategyId}, status={self.status})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, Tasks)
            and self.id == other.id
            and self.externalTaskId == other.externalTaskId
            and self.gameId == other.gameId
            and self.strategyId == other.strategyId
            and self.status == other.status
        )

    def __hash__(self):
        return hash(
            (self.id, self.externalTaskId, self.gameId, self.strategyId, self.status)
        )
