from typing import Optional

from pydantic import BaseModel, Field


class UserActions(BaseModel):
    """
    Base schema representing a stored user action event.

    Attributes:
        userId (str): Internal user identifier.
        action (str): Action/event type.
        data (Optional[dict]): Structured metadata associated with the action.
    """

    userId: str = Field(
        ...,
        description="Internal UUID of the user (serialized as string).",
        examples=["8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d"],
    )
    action: str = Field(
        ...,
        description="Action type/event key.",
        examples=["TASK_COMPLETED"],
    )
    data: Optional[dict] = Field(
        ...,
        description="Additional JSON metadata for the action.",
        examples=[{"source": "mobile-app", "durationSeconds": 84}],
    )


class CreateUserBodyActions(BaseModel):
    """
    Request schema to create a user action.

    Attributes:
        typeAction (str): Action/event type.
        data (Optional[dict]): Additional action metadata in JSON format.
        description (Optional[str]): Human-readable action description.
        apiKey_used (Optional[str]): API key used in the originating request.
    """

    typeAction: str = Field(
        ...,
        description="Action type/event identifier.",
        examples=["LOGIN"],
    )
    data: Optional[dict] = Field(
        ...,
        description="Action metadata payload.",
        examples=[{"source": "mobile-app", "ip": "203.0.113.10"}],
    )
    description: Optional[str] = Field(
        ...,
        description="Human-readable description of the action.",
        examples=["User logged in from mobile app"],
    )
    apiKey_used: Optional[str] = Field(
        ...,
        description="API key used to issue the request (if API-key based).",
        examples=["gk_live_3f6a9e0f1a2b4c5d6e7f8a9b"],
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative action-creation payload.
        """
        return {
            "typeAction": "LOGIN",
            "data": {"source": "mobile-app", "ip": "203.0.113.10"},
            "description": "User logged in from mobile app",
        }


class CreateUserActions(CreateUserBodyActions):
    """
    Internal schema for persisting user actions.

    Attributes:
        userId (str): Internal user identifier associated with the action.
    """

    userId: str = Field(
        ...,
        description="Internal UUID of the user linked to this action.",
        examples=["8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d"],
    )


class CreatedUserActions(BaseModel):
    """
    Response schema returned after creating a user action.

    Attributes:
        typeAction (str): Persisted action type.
        description (Optional[str]): Persisted action description.
        userId (str): Internal user identifier.
        is_user_created (Optional[bool]): Indicates whether the user was created
          automatically during the operation.
        message (str): Operation result message.
    """

    typeAction: str = Field(
        ...,
        description="Action type stored in the system.",
        examples=["LOGIN"],
    )
    description: Optional[str] = Field(
        ...,
        description="Human-readable description of the stored action.",
        examples=["User logged in from mobile app"],
    )
    userId: str = Field(
        ...,
        description="Internal UUID of the affected user.",
        examples=["8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d"],
    )
    is_user_created: Optional[bool] = Field(
        ...,
        description="True if user was auto-created before action insertion.",
        examples=[False],
    )
    message: str = Field(
        ...,
        description="Operation outcome message.",
        examples=["Action added successfully"],
    )
