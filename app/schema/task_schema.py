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
    """
    Base model for a task

    Attributes:
        externalTaskId (str): External task ID
        gameId (UUID): Game ID
    """
    externalTaskId: str
    gameId: UUID


class AsignPointsToExternalUserId(BaseModel):
    """
    Model for assigning points to an external user ID

    Attributes:
        externalUserId (str): External user ID
        data (Optional[dict]): Additional data
    """
    externalUserId: str
    data: Optional[dict]


class CreateTaskPost(BaseModel):
    """
    Model for creating a task

    Attributes:
        externalTaskId (str): External task ID
        strategyId (Optional[str]): Strategy ID
        params (Optional[List[CreateTaskParams]]): Task parameters
    """
    externalTaskId: str
    strategyId: Optional[str]
    params: Optional[List[CreateTaskParams]]

    def example():
        return {
            "externalTaskId": "string",
            "strategyId": "default",
            "params": [
                CreateTaskParams.example()

            ]
        }


class PostFindTask(FindBase, metaclass=AllOptional):  # noqa
    """
    Model for finding tasks

    Inherits attributes from FindBase.
    """
    ...


class FoundTask(ModelBaseInfo):
    """
    Model for a found task

    Attributes:
        externalTaskId (str): External task ID
        gameParams (Optional[List[CreateGameParams]]): Game parameters
        taskParams (Optional[List[CreateTaskParams]]): Task parameters
        strategy (Optional[Strategy]): Strategy
    """
    externalTaskId: str
    gameParams: Optional[List[CreateGameParams]]
    taskParams: Optional[List[CreateTaskParams]]
    strategy: Optional[Strategy]


class FoundTasks(BaseModel):
    """
    Model for found tasks

    Attributes:
        items (Optional[List[FoundTask]]): List of found tasks
        search_options (Optional[SearchOptions]): Search options
    """
    items: Optional[List[FoundTask]]
    search_options: Optional[SearchOptions]


class CreateTask(CreateTaskPost, metaclass=AllOptional):
    """
    Model for creating a task

    Attributes:
        gameId (str): Game ID
    """
    gameId: str


class FindTask(FindBase, metaclass=AllOptional):
    """
    Model for finding a task

    Attributes:
        gameId (UUID): Game ID
    """
    gameId: UUID


class CreateTaskPostSuccesfullyCreated(SuccesfullyCreated):
    """
    Model for successful task creation response

    Attributes:
        externalTaskId (str): External task ID
        externalGameId (str): External game ID
        gameParams (Optional[List[CreateGameParams]]): Game parameters
        taskParams (Optional[List[CreateTaskParams]]): Task parameters
        strategy (Optional[Strategy]): Strategy
    """
    externalTaskId: str
    externalGameId: str
    gameParams: Optional[List[CreateGameParams]]
    taskParams: Optional[List[CreateTaskParams]]
    strategy: Optional[Strategy]


class AssignedPointsToExternalUserId(BaseModel):
    """
    Model for assigning points to an external user ID

    Attributes:
        points (int): Points
        caseName (str): Case name
        isACreatedUser (bool): Is a created user
        gameId (UUID): Game ID
        externalTaskId (str): External task ID
        created_at (str): Created date
    """
    points: int
    caseName: str
    isACreatedUser: bool
    gameId: UUID
    externalTaskId: str
    created_at: str


class TaskPointsResponseByUser(BaseTask):
    """
    Model for task points response by user

    Attributes:
        taskId (str): Task ID
        externalTaskId (str): External task ID
        gameId (str): Game ID
        points (Optional[int]): Points
    """
    taskId: str
    externalTaskId: str
    gameId: str
    points: Optional[int]


class BaseUser(BaseModel):
    """
    Base model for a user

    Attributes:
        externalUserId (str): External user ID
        created_at (Optional[str]): Created date
    """
    externalUserId: str
    created_at: Optional[str]


class BaseUserFirstAction(BaseUser):
    """
    Model for a user's first action

    Attributes:
        firstAction (Optional[str]): First action
    """
    firstAction: Optional[str]


class TasksWithUsers(BaseModel):
    """
    Model for tasks with users

    Attributes:
        externalTaskId (str): External task ID
        users (List[BaseUserFirstAction]): List of users
    """
    externalTaskId: str
    users: List[BaseUserFirstAction]
