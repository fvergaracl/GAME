from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, Field, ForeignKey, String

from app.model.base_model import BaseModel


class Tasks(BaseModel, table=True):
    """
    Represents a task in the game.

    Attributes:
        externalTaskId (str): The ID of the external task.
        gameId (str): The ID of the game to which the task belongs.
        strategyId (str): The ID of the strategy associated with the task (optional).
    """

    externalTaskId: str = Field(sa_column=Column(String, unique=False))

    gameId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("games.id")))

    strategyId: str = Field(sa_column=Column(
        String, nullable=False, default="default"))

    class Config:
        orm_mode = True

    def __str__(self):
        return (
            f"Tasks(id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, externalTaskId={self.externalTaskId}, "
            f"gameId={self.gameId}, strategyId={self.strategyId})"
        )

    def __repr__(self):
        return (
            f"Tasks(id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, externalTaskId={self.externalTaskId}, "
            f"gameId={self.gameId}, strategyId={self.strategyId})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, Tasks)
            and self.id == other.id
            and self.externalTaskId == other.externalTaskId
            and self.gameId == other.gameId
            and self.strategyId == other.strategyId
        )

    def __hash__(self):
        return hash((self.externalTaskId, self.gameId, self.strategyId))
