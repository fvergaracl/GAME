from typing import Optional

from pydantic import BaseModel


class BaseTaskParams(BaseModel):
    """
    Base model for task parameters

    Attributes:
        key (str): Parameter key
        value (str | int | float | bool): Parameter value
    """

    key: str
    value: str | int | float | bool | dict

    class Config:
        orm_mode = True


class CreateTaskParams(BaseTaskParams):
    """Model for creating task parameters."""

    ...

    def example():
        return {"key": "variable_bonus_points", "value": 20}


class InsertTaskParams(BaseTaskParams):
    """
    Model for inserting task parameters

    Attributes:
        taskId (str): Task ID
    """

    taskId: str
    apiKey_used: Optional[str]
