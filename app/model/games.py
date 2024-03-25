from datetime import datetime

from sqlmodel import Column, DateTime, Field, String

from app.model.base_model import BaseModel


class Games(BaseModel, table=True):
    """
    Represents a game entity.

    Attributes:
        externalGameId (str): The external ID of the game.
        platform (str): The platform on which the game is played.
    """

    externalGameId: str = Field(sa_column=Column(String, unique=True))
    strategyId: str = Field(sa_column=Column(
        String), nullable=False, default="default")
    platform: str = Field(sa_column=Column(String), nullable=False)

    class Config:  # noqa
        orm_mode = True  # noqa

    def __str__(self):
        return f" Games: (id= {self.id}, created_at= {self.created_at}, updated_at= {self.updated_at}, externalGameId= {self.externalGameId}, strategyId= {self.strategyId}, platform= {self.platform})"  # noqa

    def __repr__(self):
        return f" Games: (id= {self.id}, created_at= {self.created_at}, updated_at= {self.updated_at}, externalGameId= {self.externalGameId}, strategyId= {self.strategyId}, platform= {self.platform})"  # noqa

    def __eq__(self, other):
        return (
            isinstance(other, Games)
            and self.externalGameId == other.externalGameId
            and self.platform == other.platform
        )

    def __hash__(self):
        return hash((self.externalGameId, self.platform))
