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
        return f"Strategy(id={self.id}, strategyName={self.strategyName}, data={self.data})"

    def __repr__(self):
        return f"Strategy(id={self.id}, strategyName={self.strategyName}, data={self.data})"

    def __eq__(self, other):
        return (
            self.id == other.id
            and self.strategyName == other.strategyName
            and self.data == other.data
        )

    def __hash__(self):
        return hash((self.id, self.strategyName, self.data))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.id < other.id

    def __le__(self, other):
        return self.id <= other.id
