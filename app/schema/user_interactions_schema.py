from pydantic import BaseModel, Field


class UserInteractionsBase(BaseModel):
    """
    Base schema representing a user-task interaction event.

    This model is used to persist and exchange interaction records generated
    when a user performs a relevant action on a task (for example completion,
    validation, or feedback).

    Attributes:
        userId (str): Internal UUID of the user (serialized as string).
        taskId (str): Internal UUID of the task (serialized as string).
        interactionType (str): Interaction category or event name.
        interactionDetail (str): Human-readable detail about the interaction.
    """

    userId: str = Field(
        ...,
        description="Internal UUID of the user that triggered the interaction.",
        example="8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
    )
    taskId: str = Field(
        ...,
        description="Internal UUID of the related task.",
        example="4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    )
    interactionType: str = Field(
        ...,
        description="Type of interaction event.",
        example="TASK_COMPLETED",
    )
    interactionDetail: str = Field(
        ...,
        description="Additional context describing what happened.",
        example="User completed task and submitted evidence from mobile app.",
    )
