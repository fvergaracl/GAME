from datetime import datetime
from typing import Optional, Dict
from uuid import UUID

from pydantic import BaseModel


class BaseUserGameConfig(BaseModel):
    """
    Base model for user-specific game configurations.

    Attributes:
        userId (str): The ID of the user (UUID)
        gameId (str): The ID of the game (UUID)
        experimentGroup (str): A/B testing group ('A' or 'B').
        configData (Optional[dict]): Custom configurations for the user in
          this game.
    """

    userId: str
    gameId: str
    experimentGroup: str
    configData: Optional[Dict] = None


class CreateUserGameConfig(BaseUserGameConfig):
    """
    Schema for creating a new user game configuration.
    """
    pass


class UpdateUserGameConfig(BaseModel):
    """
    Schema for updating an existing user game configuration.

    Attributes:
        experimentGroup (Optional[str]): A/B testing group ('A' or 'B').
        configData (Optional[dict]): Custom configurations.
    """

    experimentGroup: Optional[str] = None
    configData: Optional[Dict] = None


class UserGameConfigResponse(BaseUserGameConfig):
    """
    Schema for returning user game configuration details.

    Attributes:
        id (UUID): Unique identifier.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last update timestamp.
    """

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
