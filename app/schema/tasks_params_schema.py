from typing import Optional

from pydantic import BaseModel, Field


class BaseTaskParams(BaseModel):
    """
    Base schema for task-level strategy parameters.

    Attributes:
        key (str): Parameter key consumed by the task strategy logic.
        value (str | int | float | bool | dict): Parameter value associated
          with `key`.
    """

    key: str = Field(
        ...,
        description="Task parameter key.",
        example="variable_bonus_points",
    )
    value: str | int | float | bool | dict = Field(
        ...,
        description="Task parameter value (supports scalar values and objects).",
        example=20,
    )

    class Config:
        orm_mode = True


class CreateTaskParams(BaseTaskParams):
    """
    Public payload schema for creating task parameters.
    """

    ...

    def example():
        return {"key": "variable_bonus_points", "value": 20}


class InsertTaskParams(BaseTaskParams):
    """
    Internal schema used to persist task parameters.

    Attributes:
        taskId (str): Internal task identifier.
        apiKey_used (Optional[str]): API key used in the originating request.
    """

    taskId: str = Field(
        ...,
        description="Internal UUID of the task (serialized as string).",
        example="2a18d9a9-8eb5-4d33-a7bd-9590ea7ea41e",
    )
    apiKey_used: Optional[str] = Field(
        default=None,
        description="API key used to create this task parameter.",
        example="gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
    )
