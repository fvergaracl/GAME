from sqlmodel import Field, SQLModel, Column, String, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.model.base_model import BaseModel


class UserGameConfig(BaseModel, table=True):
    """
    Stores user-specific configuration for each game.

    Attributes:
        userId (str): The ID of the user.
        gameId (str): The ID of the game.
        experimentGroup (str): A/B testing group ('A' or 'B').
        configData (dict): Custom configurations for the user in this game.
    """

    userId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("users.id")))
    gameId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("games.id")))
    experimentGroup: str = Field(sa_column=Column(String), nullable=False)
    configData: dict = Field(sa_column=Column(JSON), nullable=True)

    class Config:
        orm_mode = True

    def __str__(self):
        return (
            f"UserGameConfig: (id={self.id}, userId={self.userId}, "
            f"gameId={self.gameId}, experimentGroup={self.experimentGroup}, "
            f"configData={self.configData}, created_at={self.created_at}, "
            f"updated_at={self.updated_at})"
        )

    def __repr__(self):
        return (
            f"UserGameConfig: (id={self.id}, userId={self.userId}, "
            f"gameId={self.gameId}, experimentGroup={self.experimentGroup}, "
            f"configData={self.configData}, created_at={self.created_at}, "
            f"updated_at={self.updated_at})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, UserGameConfig)
            and self.id == other.id
            and self.userId == other.userId
            and self.gameId == other.gameId
            and self.experimentGroup == other.experimentGroup
            and self.configData == other.configData
            and self.created_at == other.created_at
            and self.updated_at == other.updated_at
        )
