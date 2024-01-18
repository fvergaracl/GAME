"""
CREATE TABLE Tasks (
  id SERIAL PRIMARY KEY,
  externalTaskID VARCHAR(255) UNIQUE,
  strategyId INT,
  FOREIGN KEY (gameId) REFERENCES Games(id)
"""

from app.model.base_model import BaseModel
from sqlmodel import Field, SQLModel, Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
import sqlalchemy as sa


class Tasks(BaseModel, table=True):
    externalTaskId: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            UUID(
                as_uuid=True
            ),
            unique=True
        )
    )
    gameId: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("games.id")
        )
    )

    def __str__(self):
        return f"Tasks(externalTaskID={self.externalTaskID}, gameId={self.gameId})"

    def __repr__(self):
        return f"Tasks(externalTaskID={self.externalTaskID}, gameId={self.gameId})"

    def __eq__(self, other):
        return self.externalTaskID == other.externalTaskID and self.gameId == other.gameId

    def __hash__(self):
        return hash((self.externalTaskID, self.gameId))

    def __lt__(self, other):
        return self.externalTaskID < other.externalTaskID and self.gameId < other.gameId

    def __le__(self, other):
        return self.externalTaskID <= other.externalTaskID and self.gameId <= other.gameId
