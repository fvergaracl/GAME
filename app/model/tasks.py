"""
CREATE TABLE Tasks (
  id SERIAL PRIMARY KEY,
  externalTaskId VARCHAR(255) UNIQUE,
  strategyId INT , -- could be null
  FOREIGN KEY (gameId) REFERENCES Games(id)
"""

from app.model.base_model import BaseModel
from sqlmodel import Field, Column, Integer, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID


class Tasks(BaseModel, table=True):
    externalTaskId: str = Field(
        sa_column=Column(
            String,
            unique=False
        )
    )

    gameId: int = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("games.id")
        )
    )

    strategyId: int = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("strategy.id")
        ),
        nullable=True
    )

    def __str__(self):
        return f"Tasks(externalTaskId={self.externalTaskId}, gameId={self.gameId})"

    def __repr__(self):
        return f"Tasks(externalTaskId={self.externalTaskId}, gameId={self.gameId})"

    def __eq__(self, other):
        return self.externalTaskId == other.externalTaskId and self.gameId == other.gameId

    def __hash__(self):
        return hash((self.externalTaskId, self.gameId))

    def __lt__(self, other):
        return self.externalTaskId < other.externalTaskId and self.gameId < other.gameId

    def __le__(self, other):
        return self.externalTaskId <= other.externalTaskId and self.gameId <= other.gameId
