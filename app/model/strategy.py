"""
CREATE TABLE Strategy (
  id SERIAL PRIMARY KEY,
  strategyName VARCHAR(255) UNIQUE
  data JSONB NOT NULL,
  FOREIGN KEY (taskId) REFERENCES Tasks(id)
);
"""

from app.model.base_model import BaseModel
from sqlmodel import Column, Field, String
from sqlalchemy.dialects.postgresql import JSONB


class Strategy(BaseModel, table=True):
    strategyName: str = Field(sa_column=Column(String, unique=True))
    data: dict = Field(sa_column=Column(JSONB), nullable=False)

    def __str__(self):
        return f"Strategy: {self.strategy}"

    def __repr__(self):
        return f"Strategy: {self.strategy}"

    def __eq__(self, other):
        return self.strategy == other.strategy

    def __hash__(self):
        return hash((self.strategy))

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.strategy < other.strategy
