from typing import List, Optional

from pydantic import BaseModel
from app.schema.base_schema import ModelBaseInfo, SearchOptions, FindBase
from app.util.schema import AllOptional


class BaseUserPointsBaseModel(BaseModel):
    points: int
    description: Optional[str]
    timestamp: str
    userId: int
    taskId: int


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
    founds: Optional[List[UserPoints]]
    search_options: Optional[SearchOptions]


class PostAssignPointsToUser(BaseModel):
    externalTaskId: str
    externalUserId: str
    points:  Optional[int]
    description: Optional[str]


class ResponseAssignPointsToUser(BaseModel):
    points: int
    description: Optional[str]
    timestamp: str
    externalTaskId: str
    externalUserId: str
    isNewUser: bool


# [(1, 'string', 129), (2, 'eeeeeeeeeeeeee', 100)]

class PointsByUserInTask(BaseModel):
    externalTaskId: str
    points: int


class ResponsePointsByExternalUserId(BaseModel):
    externalUserId: str
    points: int
    points_by_task: List[PointsByUserInTask]
