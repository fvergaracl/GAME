from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BaseGameParams(BaseModel):
    """
    Base schema for game strategy parameters.

    Attributes:
        key (str): Parameter key consumed by strategy logic.
        value (str | int | float | bool): Parameter value. Type depends on the
          target strategy variable.
    """

    key: str = Field(
        ...,
        description="Parameter key used by the game strategy.",
        example="variable_basic_points",
    )
    value: str | int | float | bool = Field(
        ...,
        description="Parameter value associated with the provided key.",
        example=10,
    )

    class Config:
        orm_mode = True


class BaseCreateGameParams(BaseGameParams):
    """
    Base payload used to create game parameters.
    """

    ...


class InsertGameParams(BaseGameParams):
    """
    Internal schema used to persist game parameters.

    Attributes:
        gameId (str): Internal game identifier.
        apiKey_used (Optional[str]): API key used to create the record.
        oauth_user_id (Optional[str]): OAuth subject that created the record.
    """

    gameId: str = Field(
        ...,
        description="Internal game identifier (UUID serialized as string).",
        example="4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    )
    apiKey_used: Optional[str] = Field(
        default=None,
        description="API key used during creation, when request is API-key based.",
        example="gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
    )
    oauth_user_id: Optional[str] = Field(
        default=None,
        description="OAuth user subject that initiated the operation.",
        example="3c95c2d7-1ce8-4ea0-b35f-6dfd19127f35",
    )


class CreateGameParams(BaseCreateGameParams):
    """
    Public schema for creating game parameters from API requests.
    """

    @staticmethod
    def example() -> dict:
        """
        Representative payload for game parameter creation.
        """
        return {"key": "variable_basic_points", "value": 10}

    ...


class BaseFindGameParams(BaseGameParams):
    """
    Read schema for returning stored game parameters.

    Attributes:
        id (UUID): Unique parameter identifier.
    """

    id: UUID = Field(
        ...,
        description="Unique identifier of the game parameter record.",
        example="fd8551f4-7cf0-4f8b-b372-a269541db5a5",
    )


class UpdateGameParams(CreateGameParams):
    """
    Payload schema for updating existing game parameters.

    Attributes:
        id (UUID): Unique parameter identifier.
        key (str): Parameter key.
        value (str | int | float | bool): Updated parameter value.
    """

    id: UUID = Field(
        ...,
        description="Identifier of the parameter record to update.",
        example="fd8551f4-7cf0-4f8b-b372-a269541db5a5",
    )
    key: str = Field(
        ...,
        description="Parameter key.",
        example="variable_basic_points",
    )
    value: str | int | float | bool = Field(
        ...,
        description="New value for the parameter key.",
        example=15,
    )
