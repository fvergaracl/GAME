"""
CREATE TABLE Tasks (
  id SERIAL PRIMARY KEY,
  externalTaskID VARCHAR(255) UNIQUE,
  strategyId INT,
  FOREIGN KEY (strategyId) REFERENCES Strategies(id)
  FOREIGN KEY (gameId) REFERENCES Games(id)
"""

from app.model.base_model import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer, String


class Tasks(BaseModel, table=True):
    externalTaskID: str = Field(sa_column=Column(String, unique=True))
    strategyId: int = Field(sa_column=Column(
        Integer, ForeignKey("strategies.id")))
    gameId: int = Field(sa_column=Column(Integer, ForeignKey("games.id")))

    def __str__(self):
        return f"Tasks: {self.externalTaskID}, {self.strategyId}"

    def __repr__(self):
        return f"Tasks: {self.externalTaskID}, {self.strategyId}"

    def __eq__(self, other):
        return self.externalTaskID == other.externalTaskID and self.strategyId == other.strategyId

    def __hash__(self):
        return hash((self.externalTaskID, self.strategyId))

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.strategyId < other.strategyId
