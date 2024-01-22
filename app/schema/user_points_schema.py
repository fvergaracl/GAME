from typing import List, Optional

from pydantic import BaseModel
from app.schema.base_schema import ModelBaseInfo, SearchOptions, FindBase
from app.util.schema import AllOptional


class BaseUserPointsBaseModel(BaseModel):
    points: int
    description: str
    timestamp: str
    userId: int
    taskId: int


class UserPoints(ModelBaseInfo, BaseUserPointsBaseModel, metaclass=AllOptional):
    ...

class FindQueryByExternalGameId(FindBase, metaclass=AllOptional):
    externalGameId: str


class FindAllUserPointsResult(BaseModel):
    founds: Optional[List[UserPoints]]
    search_options: Optional[SearchOptions]
