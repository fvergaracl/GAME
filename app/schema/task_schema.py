from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from app.schema.base_schema import (
    FindBase,
    ModelBaseInfo,
    SearchOptions,
    SuccesfullyCreated
)
from app.schema.strategy_schema import BaseStrategy
from app.util.schema import AllOptional


class BaseTask(BaseModel):
    externalTaskId: str
    gameId: UUID


class CreateTaskPost(BaseModel):
    externalTaskId: str
    strategyId: Optional[str]


class CreateTask(CreateTaskPost, metaclass=AllOptional):
    gameId: str


class Task(ModelBaseInfo, BaseTask, metaclass=AllOptional):
    ...


class FindTaskResult(BaseModel):
    items: Optional[List[Task]]
    search_options: Optional[SearchOptions]


class FindTask(FindBase, metaclass=AllOptional):
    gameId: UUID


class FindTaskByExternalGameID(FindBase, metaclass=AllOptional):
    ...
    # using gameId


class GetTaskById(BaseModel):
    taskId: UUID


class FoundTaskById(BaseModel):
    task: Task
    strategy: Optional[BaseStrategy]


class CreateTaskPostSuccesfullyCreated(SuccesfullyCreated):
    externalTaskId: str
    gameId: str
    strategy: Optional[BaseStrategy]
