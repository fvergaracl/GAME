from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, Field, ForeignKey, String

from app.model.base_model import BaseModel


class GamesParams(BaseModel, table=True):
    """
    Represents the parameters for a game.

    Attributes:
        key (str): The key of the parameter, used as an identifier.
        value (str): The value of the parameter.
        gameId (str): The ID of the game associated with this parameter,
          acting as a foreign key to the `games` table.

    Methods:
        __str__(self): Returns a string representation of the model instance,
          including the key, value, and game ID.
        __repr__(self): Returns an official string representation of the model.
        __eq__(self, other): Determines equality based on key, value, and
          gameId.
        __hash__(self): Provides a hash based on the key, value, and gameId
          attributes.

    Configurations:
        orm_mode (bool): Allows the model to be used with ORM, set to True to
          enable.
    """

    # Field definitions
    key: str = Field(sa_column=Column(String))
    value: str = Field(sa_column=Column(String))
    gameId: str = Field(sa_column=Column(UUID(as_uuid=True), ForeignKey("games.id")))
    apiKey_used: str = Field(
        sa_column=Column(String, ForeignKey("apikey.apiKey"), nullable=True)
    )
    oauthusers_id: str = Field(
        sa_column=Column(
            String, ForeignKey("oauthusers.provider_user_id"), nullable=True
        )
    )

    class Config:
        orm_mode = True

    def __str__(self):
        return (
            f"GameParams: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, key={self.key}, "
            f"value={self.value}, gameId={self.gameId})"
        )

    def __repr__(self):
        return (
            f"GameParams: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, key={self.key}, "
            f"value={self.value}, gameId={self.gameId})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, GamesParams)
            and self.key == other.key
            and self.value == other.value
            and self.gameId == other.gameId
        )

    def __hash__(self):
        return hash((self.key, self.value, self.gameId))
