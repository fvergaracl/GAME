from typing import List, Optional

from pydantic import BaseModel
from app.schema.base_schema import ModelBaseInfo, SearchOptions, FindBase
from app.schema.wallet_schema import WalletWithoutUserId
from app.util.schema import AllOptional


class PostAssignPointsToUser(BaseModel):
    taskId: str
    points:  Optional[int]
    description: Optional[str]
    data: Optional[dict]


class BaseUserPointsBaseModel(PostAssignPointsToUser):
    userId: str


class UserPointsAssigned(ModelBaseInfo, BaseUserPointsBaseModel):
    userId: str
    taskId: str
    wallet: Optional[WalletWithoutUserId]
    description: Optional[str]
    message: Optional[str] = "Successfully assigned"


class UserPoints(
    ModelBaseInfo,
    BaseUserPointsBaseModel,
    metaclass=AllOptional
):
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
