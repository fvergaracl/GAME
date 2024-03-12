from uuid import UUID
from pydantic import BaseModel


class BaseTaskParams(BaseModel):
    key: str
    value: str | int | float | bool

    class Config:
        orm_mode = True


class BaseCreateTaskParams(BaseTaskParams):
    ...


class CreateTaskParams(BaseTaskParams):
    ...


class InsertTaskParams(BaseTaskParams):
    taskId: str


class BaseFindTaskParams(BaseTaskParams):
    ...
    id: UUID


class UpdateTaskarams(CreateTaskParams):
    id: UUID
    key: str
    value: str | int | float | bool
