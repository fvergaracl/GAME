from typing import List, Optional
from pydantic import BaseModel
from app.schema.base_schema import ModelBaseInfo
from app.schema.wallet_schema import WalletWithoutUserId
from app.util.schema import AllOptional


class PostAssignPointsToUser(BaseModel):
    """
    Model for assigning points to a user

    Attributes:
        taskId (str): Task ID
        caseName (Optional[str]): Case name
        points (Optional[int]): Points
        description (Optional[str]): Description
        data (Optional[dict]): Additional data
    """
    taskId: str
    caseName: Optional[str]
    points: Optional[int]
    description: Optional[str]
    data: Optional[dict]


class PointsAssigned(BaseModel):
    """
    Model for assigned points

    Attributes:
        points (int): Points
        timesAwarded (int): Times awarded
    """
    points: int
    timesAwarded: int


class PointsData(BaseModel):
    """
    Model for points data

    Attributes:
        points (int): Points
        caseName (str): Case name
        created_at (str): Created date
    """
    points: int
    caseName: str
    created_at: str


class PointsAssignedToUser(PointsAssigned):
    """
    Model for points assigned to a user

    Attributes:
        externalUserId (str): External user ID
        pointsData (Optional[List[PointsData]]): Points data
    """
    externalUserId: str
    pointsData: Optional[List[PointsData]]


class PointsAssignedToUserWithDetails(PointsAssignedToUser):  # noqa
    """Model for points assigned to a user with details."""
    pointsData: List[PointsAssignedToUser]


class TaskPointsByGame(BaseModel):
    """
    Model for task points by game

    Attributes:
        externalTaskId (str): External task ID
        points (List[PointsAssignedToUser]): Points assigned to user
    """
    externalTaskId: str
    points: List[PointsAssignedToUser]


class AllPointsByGame(BaseModel):
    """
    Model for all points by game

    Attributes:
        externalGameId (str): External game ID
        created_at (str): Created date
        task (List[TaskPointsByGame]): List of task points by game
    """
    externalGameId: str
    created_at: str
    task: List[TaskPointsByGame]


class BaseUserPointsBaseModel(PostAssignPointsToUser):
    """
    Base model for user points

    Attributes:
        userId (str): User ID
    """
    userId: str


class UserPointsAssign(BaseUserPointsBaseModel):
    """Model for user points assignment."""
    ...


class UserPointsAssigned(ModelBaseInfo, BaseUserPointsBaseModel):
    """
    Model for user points assignment response

    Attributes:
        userId (str): User ID
        taskId (str): Task ID
        wallet (Optional[WalletWithoutUserId]): Wallet
        description (Optional[str]): Description
        message (Optional[str]): Success message
    """
    userId: str
    taskId: str
    wallet: Optional[WalletWithoutUserId]
    description: Optional[str]
    message: Optional[str] = "Successfully assigned"


class UserPoints(
        ModelBaseInfo, BaseUserPointsBaseModel, metaclass=AllOptional
):
    """Model for user points."""
    ...


class ResponseGetPointsByTask(BaseModel):
    """
    Model for points by task response

    Attributes:
        externalUserId (str): External user ID
        points (int): Points
    """
    externalUserId: str
    points: int


class PointsDetail(BaseModel):
    """
    Model for points detail

    Attributes:
        points (int): Points
        caseName (str): Case name
        created_at (str): Created date
    """
    points: int
    caseName: str
    created_at: str


class TaskDetail(BaseModel):
    """
    Model for task detail

    Attributes:
        externalTaskId (str): External task ID
        pointsData (List[PointsDetail]): Points data
    """
    externalTaskId: str
    pointsData: List[PointsDetail]


class GameDetail(BaseModel):
    """
    Model for game detail

    Attributes:
        externalGameId (str): External game ID
        points (int): Points
        timesAwarded (int): Times awarded
        tasks (List[TaskDetail]): List of task details
    """
    externalGameId: str
    points: int
    timesAwarded: int
    tasks: List[TaskDetail]


class UserGamePoints(BaseModel):
    """
    Model for user game points

    Attributes:
        externalUserId (str): External user ID
        points (int): Points
        timesAwarded (int): Times awarded
        games (List[GameDetail]): List of game details
        userExists (Optional[bool]): If the user exists
    """
    externalUserId: str
    points: int
    timesAwarded: int
    games: List[GameDetail]
    userExists: Optional[bool] = True


class ResponseGetPointsByGame(BaseModel):
    """
    Model for points by game response

    Attributes:
        externalTaskId (str): External task ID
        points (List[ResponseGetPointsByTask]): Points by task
    """
    externalTaskId: str
    points: List[ResponseGetPointsByTask]


class PointsByUserInTask(BaseModel):
    """
    Model for points by user in task

    Attributes:
        externalTaskId (str): External task ID
        points (int): Points
    """
    externalTaskId: str
    points: int


class ResponsePointsByExternalUserId(BaseModel):
    """
    Model for points by external user ID response

    Attributes:
        externalUserId (str): External user ID
        points (int): Points
        points_by_task (List[PointsByUserInTask]): Points by task
    """
    externalUserId: str
    points: int
    points_by_task: List[PointsByUserInTask]
