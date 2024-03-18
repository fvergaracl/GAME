from uuid import UUID
from pydantic import BaseModel


class BaseTaskParams(BaseModel):
    key: str
    value: str | int | float | bool

    class Config:  # noqa
        orm_mode = True  # noqa


class CreateTaskParams(BaseTaskParams):
    ...


class InsertTaskParams(BaseTaskParams):
    taskId: str
