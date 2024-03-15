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


class PointsAssignedToUser(BaseModel):
    externalUserId: str
    points: int
    timesAwarded: int


class PointsAssignedToUserWithDetails(PointsAssignedToUser):
    pointsData: List[dict]



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


class UserPoints(ModelBaseInfo, BaseUserPointsBaseModel, metaclass=AllOptional):
    ...


class FindQueryByExternalGameId(FindBase, metaclass=AllOptional):
    externalGameId: str


class FindQueryByExternalTaskId(FindBase, metaclass=AllOptional):
    externalTaskId: str


class FindQueryByExternalUserId(FindBase, metaclass=AllOptional):
    externalUserId: str


class FindQueryByExternalTaskIdExternalUserId(FindBase, metaclass=AllOptional):
    externalTaskId: str
    externalUserId: str


class FindAllUserPointsResult(BaseModel):
    items: Optional[List[UserPoints]]
    search_options: Optional[SearchOptions]


class ResponseAssignPointsToUser(BaseModel):
    points: int
    data: Optional[dict]
    externalTaskId: str
    externalUserId: str
    isNewUser: Optional[bool]


class ResponseGetPointsByTask(BaseModel):
    externalUserId: str
    points: int


class ResponseGetPointsByGame(BaseModel):
    externalTaskId: str
    points: List[ResponseGetPointsByTask]


class ResponseGetPointsByTasks(BaseModel, metaclass=AllOptional):
    items: Optional[List[ResponseGetPointsByTask]]


class PointsByUserInTask(BaseModel):
    externalTaskId: str
    points: int


class ResponsePointsByExternalUserId(BaseModel):
    externalUserId: str
    points: int
    points_by_task: List[PointsByUserInTask]
