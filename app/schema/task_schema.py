from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schema.tasks_params_schema import CreateTaskParams
from app.schema.games_params_schema import CreateGameParams
from app.schema.base_schema import (
    FindBase, ModelBaseInfo, SearchOptions, SuccesfullyCreated
)
from app.schema.strategy_schema import Strategy
from app.util.schema import AllOptional


class BaseTask(BaseModel):
    externalTaskId: str
    gameId: UUID


class AsignPointsToExternalUserId(BaseModel):  # noqa
    externalUserId: str
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


class PostFindTask(FindBase, metaclass=AllOptional):  # noqa
    ...


class FoundTask(ModelBaseInfo):
    externalTaskId: str
    gameParams: Optional[List[CreateGameParams]]
    taskParams: Optional[List[CreateTaskParams]]
    strategy: Optional[Strategy]


class FoundTasks(BaseModel):  # noqa
    items: Optional[List[FoundTask]]
    search_options: Optional[SearchOptions]


class CreateTask(CreateTaskPost, metaclass=AllOptional):
    gameId: str


class FindTask(FindBase, metaclass=AllOptional):
    gameId: UUID


class CreateTaskPostSuccesfullyCreated(SuccesfullyCreated):
    externalTaskId: str
    externalGameId: str
    gameParams: Optional[List[CreateGameParams]]
    taskParams: Optional[List[CreateTaskParams]]
    strategy: Optional[Strategy]


class AssignedPointsToExternalUserId(BaseModel):
    points: int
    caseName: str
    isACreatedUser: bool


class TaskPointsResponseByUser(BaseTask):
    taskId: str
    externalTaskId: str
    gameId: str
    points: Optional[int]


class BaseUser(BaseModel):
    externalUserId: str
    created_at: Optional[str]


class TasksWithUsers(BaseModel):
    externalTaskId: str
    users: List[BaseUser]
