from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schema.tasks_params_schema import CreateTaskParams
from app.schema.games_params_schema import CreateGameParams
from app.schema.base_schema import (FindBase, ModelBaseInfo, SearchOptions,
                                    SuccesfullyCreated)
from app.schema.strategy_schema import Strategy
from app.util.schema import AllOptional


class BaseTask(BaseModel):
    externalTaskId: str
    gameId: UUID


class AsignPointsToExternalUserId(BaseModel):
    externalUserId: str
    points: Optional[int]
    data: Optional[dict]


class CreateTaskPost(BaseModel):
    externalTaskId: str
    strategyId: Optional[str]
    params: Optional[List[CreateTaskParams]]

    def example():
        return {
            "externalTaskId": "string",
            "strategyId": "default",
            "params": [
                {
                    "key": "variable_bonus_points",
                    "value": 20
                }
            ]
        }


class PostFindTask(FindBase, metaclass=AllOptional):
    ...


class FoundTask(ModelBaseInfo):
    externalTaskId: str
    gameParams: Optional[List[CreateGameParams]]
    taskParams: Optional[List[CreateTaskParams]]
    strategy: Optional[Strategy]


class FoundTasks(BaseModel):
    items: Optional[List[FoundTask]]
    search_options: Optional[SearchOptions]


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
    strategy: Optional[Strategy]


class CreateTaskPostSuccesfullyCreated(SuccesfullyCreated):
    externalTaskId: str
    externalGameId: str
    gameParams: Optional[List[CreateGameParams]]
    taskParams: Optional[List[CreateTaskParams]]
    strategy: Optional[Strategy]


class TaskPoints(BaseModel):
    userId: UUID  # userId
    externalUserId: str
    points: int


class TaskPointsResponse(BaseModel):
    externalTaskId: str
    points: Optional[List[TaskPoints]]


class TaskPointsResponseByUser(BaseTask):
    taskId: str
    externalTaskId: str
    gameId: str
    points: Optional[int]
