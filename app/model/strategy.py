from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, String

from app.model.base_model import BaseModel


class Strategy(BaseModel, table=True):
    """
    Represents a strategy in the application.

    Attributes:
        strategyName (str): The name of the strategy.
        data (dict): Additional data associated with the strategy.
    """

    strategyName: str = Field(sa_column=Column(String, unique=True))
    data: dict = Field(sa_column=Column(JSONB), nullable=False)

    def __str__(self):
        return (
            f"Strategy(id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, strategyName={self.strategyName}, "
            f"data={self.data})"
        )

    class Config:
        orm_mode = True

    def __repr__(self):
        return (
            f"Strategy(id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, strategyName={self.strategyName}, "
            f"data={self.data})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, Strategy)
            and self.strategyName == other.strategyName
            and self.data == other.data
        )

    def make_hashable(self, obj):
        if isinstance(obj, (tuple, list)):
            return tuple(self.make_hashable(e) for e in obj)
        elif isinstance(obj, dict):
            return tuple(sorted((k, self.make_hashable(v)) for k, v in obj.items()))
        else:
            return obj

    def __hash__(self):
        data_as_hashable = self.make_hashable(self.data)
        return hash((self.strategyName, data_as_hashable))
