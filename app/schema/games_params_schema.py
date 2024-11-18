from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class BaseGameParams(BaseModel):
    """
    Base model for game parameters

    Attributes:
        key (str): Parameter key
        value (str | int | float | bool): Parameter value
    """

    key: str
    value: str | int | float | bool

    class Config:
        orm_mode = True


class BaseCreateGameParams(BaseGameParams):
    """Model for creating game parameters."""

    ...


class InsertGameParams(BaseGameParams):
    """
    Model for inserting game parameters

    Attributes:
        gameId (str): Game ID
    """

    gameId: str
    apiKey_used: Optional[str]
    oauth_user_id: Optional[str]


class CreateGameParams(BaseCreateGameParams):
    """Model for creating game parameters."""

    ...


class BaseFindGameParams(BaseGameParams):
    """
    Model for finding game parameters

    Attributes:
        id (UUID): Unique identifier
    """

    id: UUID


class UpdateGameParams(CreateGameParams):
    """
    Model for updating game parameters

    Attributes:
        id (UUID): Unique identifier
        key (str): Parameter key
        value (str | int | float | bool): Parameter value
    """

    id: UUID
    key: str
    value: str | int | float | bool
