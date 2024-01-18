from typing import List, Optional

from pydantic import BaseModel
from app.schema.base_schema import FindBase, ModelBaseInfo, SearchOptions
from app.util.schema import AllOptional


class BaseTask(BaseModel):
    externalTaskID: str
    gameId: str


class Task(ModelBaseInfo, BaseTask, metaclass=AllOptional):
    ...


class FindTaskResult(BaseModel):
    founds: Optional[List[Task]]
    search_options: Optional[SearchOptions]

class FindTask(FindBase, BaseTask, metaclass=AllOptional):
    ...