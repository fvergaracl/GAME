from typing import List, Optional

from pydantic import BaseModel

from app.schema.base_schema import FindBase, ModelBaseInfo, SearchOptions
from app.schema.wallet_schema import WalletWithoutUserId
from app.util.schema import AllOptional


class PostAssignPointsToUser(BaseModel):
    taskId: str
    caseName: Optional[str]
    points: Optional[int]
    description: Optional[str]
    data: Optional[dict]


class PointsAssigned(BaseModel):
    points: int
    timesAwarded: int


class PointsAssignedToUser(PointsAssigned):
    externalUserId: str


class PointsAssignedToUserWithDetails(PointsAssignedToUser):  # noqa
    pointsData: List[PointsAssignedToUser]


class TaskPointsByGame(BaseModel):
    externalTaskId: str
    points: List[PointsAssignedToUser]


class AllPointsByGame(BaseModel):
    externalGameId: str
    created_at: str
    task: List[TaskPointsByGame]


class BaseUserPointsBaseModel(PostAssignPointsToUser):
    userId: str


class UserPointsAssign(BaseUserPointsBaseModel):
    ...


class UserPointsAssigned(ModelBaseInfo, BaseUserPointsBaseModel):
    userId: str
    taskId: str
    wallet: Optional[WalletWithoutUserId]
    description: Optional[str]
    message: Optional[str] = "Successfully assigned"


class UserPoints(
        ModelBaseInfo, BaseUserPointsBaseModel, metaclass=AllOptional
):
    ...


class ResponseGetPointsByTask(BaseModel):
    externalUserId: str
    points: int


class ResponseGetPointsByGame(BaseModel):
    externalTaskId: str
    points: List[ResponseGetPointsByTask]


class PointsByUserInTask(BaseModel):
    externalTaskId: str
    points: int


class ResponsePointsByExternalUserId(BaseModel):
    externalUserId: str
    points: int
    points_by_task: List[PointsByUserInTask]
