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

    gameId: str = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("games.id")
        )
    )

    strategyId: str = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("strategy.id")
        ),
        nullable=True
    )

    def __str__(self):
        return f"Tasks(id={self.id}, externalTaskId={self.externalTaskId}, gameId={self.gameId}, strategyId={self.strategyId})"

    def __repr__(self):
        return f"Tasks(id={self.id}, externalTaskId={self.externalTaskId}, gameId={self.gameId}, strategyId={self.strategyId})"

    def __eq__(self, other):
        return (
            self.id == other.id
            and self.externalTaskId == other.externalTaskId
            and self.gameId == other.gameId
            and self.strategyId == other.strategyId
        )

    def __hash__(self):
        return hash((self.id, self.externalTaskId, self.gameId, self.strategyId))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.id < other.id

    def __le__(self, other):
        return self.id <= other.id
