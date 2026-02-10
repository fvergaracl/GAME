from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BaseUserGameConfig(BaseModel):
    """
    Base schema for user-specific game configuration overrides.

    Attributes:
        userId (str): Internal user identifier (UUID serialized as string).
        gameId (str): Internal game identifier (UUID serialized as string).
        experimentGroup (str): Experiment or cohort group label
          (for example `A`, `B`, `control`, `treatment`).
        configData (Optional[dict]): User-specific configuration payload for
          the game context.
    """

    userId: str = Field(
        ...,
        description="Internal UUID of the user (serialized as string).",
        example="8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
    )
    gameId: str = Field(
        ...,
        description="Internal UUID of the game (serialized as string).",
        example="4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    )
    experimentGroup: str = Field(
        ...,
        description="Experiment/campaign group assigned to the user.",
        example="A",
    )
    configData: Optional[Dict] = Field(
        default=None,
        description="Custom configuration object applied to this user-game pair.",
        example={"incentiveMultiplier": 1.1, "featureFlags": {"new_reward_rule": True}},
    )


class CreateUserGameConfig(BaseUserGameConfig):
    """
    Request schema for creating a user-game configuration record.
    """

    @staticmethod
    def example() -> dict:
        """
        Returns a representative payload for user game configuration creation.
        """
        return {
            "userId": "8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
            "gameId": "4ce32be2-77f6-4ffc-8e07-78dc220f0520",
            "experimentGroup": "A",
            "configData": {"incentiveMultiplier": 1.1},
        }


class UpdateUserGameConfig(BaseModel):
    """
    Schema for updating an existing user game configuration.

    Attributes:
        experimentGroup (Optional[str]): Updated experiment/campaign group.
        configData (Optional[dict]): Updated custom configuration payload.
    """

    experimentGroup: Optional[str] = Field(
        default=None,
        description="Updated experiment/campaign group for the user-game pair.",
        example="B",
    )
    configData: Optional[Dict] = Field(
        default=None,
        description="Updated custom configuration object.",
        example={"incentiveMultiplier": 1.2},
    )


class UserGameConfigResponse(BaseUserGameConfig):
    """
    Schema for returning user game configuration details.

    Attributes:
        id (UUID): Unique identifier of the configuration record.
        created_at (datetime): UTC creation timestamp.
        updated_at (datetime): UTC last update timestamp.
    """

    id: UUID = Field(
        ...,
        description="Unique UUID of the user-game configuration record.",
        example="fd8551f4-7cf0-4f8b-b372-a269541db5a5",
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the record was created.",
        example="2026-02-10T12:20:00Z",
    )
    updated_at: datetime = Field(
        ...,
        description="UTC timestamp when the record was last updated.",
        example="2026-02-10T12:35:00Z",
    )

    class Config:
        orm_mode = True
