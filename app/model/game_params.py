from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, Field, ForeignKey, String

from app.model.base_model import BaseModel


class GamesParams(BaseModel, table=True):
    """
    Represents the parameters for a game.

    Attributes:
        key (str): The key of the parameter.
        value (str): The value of the parameter.
        gameId (str): The ID of the game associated with the parameter.
    """

    key: str = Field(sa_column=Column(String))
    value: str = Field(sa_column=Column(String))
    gameId: str = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("games.id")))

    class Config:   # noqa
        orm_mode = True  # noqa

    def __str__(self):
        return f"GameParams: (id={self.id}, created_at={self.created_at}, updated_at={self.updated_at}, key={self.key}, value={self.value}, gameId={self.gameId})"

    def __repr__(self):
        return f"GameParams: (id={self.id}, created_at={self.created_at}, updated_at={self.updated_at}, key={self.key}, value={self.value}, gameId={self.gameId})"

    def __eq__(self, other):
        return (
            isinstance(other, GamesParams)
            and self.key == other.key
            and self.value == other.value
            and self.gameId == other.gameId
        )

    def __hash__(self):
        return hash((self.key, self.value, self.gameId))
