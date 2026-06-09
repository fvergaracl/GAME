from pydantic import ConfigDict
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, Field, ForeignKey, String

from app.model.base_model import BaseModel


class Tasks(BaseModel, table=True):
    """Table for tasks associated with games.

    A task is an activity inside a game, uniquely identified by an external
    id. It is linked to a specific game and may carry its own strategy;
    otherwise it inherits the game's strategy.

    Attributes:
        externalTaskId (str): Caller-supplied identifier, unique per game, so
            a task can be referenced from outside the system.
        gameId (UUID): Foreign key to the ``games`` table.
        strategyId (str): Identifier of the strategy bound to this task.
            Defaults to ``default`` and is non-nullable, so every task always
            has a strategy.
        status (str): Lifecycle status of the task; defaults to ``open``.
        apiKey_used (str): The API key that created the task (audit + scope).
    """

    externalTaskId: str = Field(sa_column=Column(String, nullable=False))
    gameId: str = Field(sa_column=Column(UUID(as_uuid=True), ForeignKey("games.id")))
    strategyId: str = Field(sa_column=Column(String, nullable=False, default="default"))
    status: str = Field(sa_column=Column(String, nullable=False, default="open"))
    apiKey_used: str = Field(
        sa_column=Column(String, ForeignKey("apikey.apiKey"), nullable=True)
    )

    model_config = ConfigDict(from_attributes=True)

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
