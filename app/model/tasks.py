from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, Field, ForeignKey, String

from app.model.base_model import BaseModel


class Tasks(BaseModel, table=True):
    """
    Defines the `Tasks` table for managing tasks associated with games in a SQL database.

    This model represents a task entity within a gaming context, uniquely identified by an external ID.
    Tasks are linked to specific games by their IDs and optionally associated with a strategy.

    Attributes:
        externalTaskId (str): A unique identifier for the task from an external source.
        gameId (UUID): A UUID corresponding to the game this task is associated with, establishing a foreign key relationship with the `games` table.
        strategyId (str): An identifier for the strategy linked to this task, with a default value if not specified. This field is not nullable.
    """

    externalTaskId: str = Field(sa_column=Column(String, unique=True))
    gameId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("games.id")))
    strategyId: str = Field(sa_column=Column(
        String, nullable=False, default="default"))

    class Config:
        orm_mode = True

    def __str__(self):
        return (
            f"Tasks(id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at},"
            f"externalTaskId={self.externalTaskId}, gameId={self.gameId}, "
            f"strategyId={self.strategyId})")

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (isinstance(other, Tasks) and self.id == other.id and
                self.externalTaskId == other.externalTaskId and
                self.gameId == other.gameId and
                self.strategyId == other.strategyId)

    def __hash__(self):
        return hash((
            self.id, self.externalTaskId, self.gameId, self.strategyId)
        )
