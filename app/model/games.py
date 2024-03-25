from sqlmodel import Column, Field, String
from app.model.base_model import BaseModel


class Games(BaseModel, table=True):
    """
    Represents a game entity, identified by an external ID.

    This model stores game information and integrates with SQLModel
    for ORM capabilities. It supports operations like creating,
    updating, and querying game entities based on their external IDs,
    strategies, and platforms.

    Attributes:
        id (int): Unique identifier, from BaseModel.
        created_at (datetime): Creation timestamp, from BaseModel.
        updated_at (datetime): Last update timestamp, from BaseModel.
        externalGameId (str): Unique external game ID.
        strategyId (str): Strategy identifier, defaults to "default".
        platform (str): Platform (e.g., PC, PlayStation).

    Methods:
        __str__: Returns a string representation.
        __repr__: For debug logs, similar to __str__.
        __eq__: Equality based on externalGameId and platform.
        __hash__: Hash based on externalGameId and platform.

    Configuration:
        orm_mode (bool): Enables ORM mode for Pydantic models.
    """
    externalGameId: str = Field(sa_column=Column(String, unique=True))
    strategyId: str = Field(sa_column=Column(String),
                            nullable=False, default="default")
    platform: str = Field(sa_column=Column(String), nullable=False)

    class Config:
        orm_mode = True

    def __str__(self):
        return (
            f"Games(id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, externalGameId="
            f"{self.externalGameId}, strategyId={self.strategyId}, "
            f"platform={self.platform})"
        )

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (
            isinstance(other, Games) and
            self.externalGameId == other.externalGameId and
            self.platform == other.platform
        )

    def __hash__(self):
        return hash((self.externalGameId, self.platform))
