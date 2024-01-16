"""
CREATE TABLE Strategies (
  id SERIAL PRIMARY KEY,
  strategy VARCHAR(255) UNIQUE
);
"""

from app.model.base_model import BaseModel
from sqlmodel import Column, Field, String


class Strategies(BaseModel, table=True):
    strategy: str = Field(sa_column=Column(String, unique=True))

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
