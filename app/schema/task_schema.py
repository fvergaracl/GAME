from typing import List, Optional

from pydantic import BaseModel
from app.schema.base_schema import FindBase, ModelBaseInfo, SearchOptions, SuccesfullyCreated
from app.util.schema import AllOptional


class BaseTask(BaseModel):
    externalTaskId: str
    gameId: str


class Task(ModelBaseInfo, BaseTask, metaclass=AllOptional):
    ...


class FindTaskResult(BaseModel):
    founds: Optional[List[Task]]
    search_options: Optional[SearchOptions]


class FindTask(FindBase, metaclass=AllOptional):
    gameId: int


class FindTaskByExternalGameID(FindBase, metaclass=AllOptional):
    externalGameId: str


class CreateTaskPost(BaseModel):
    externalGameId: str
    externalTaskId: str


class CreateTaskPostSuccesfullyCreated(SuccesfullyCreated):
    externalGameId: str
    externalTaskId: str
    gameId: int
