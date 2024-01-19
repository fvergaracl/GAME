from typing import List, Optional
from pydantic import BaseModel

from app.schema.base_schema import ModelBaseInfo, SearchOptions


class BaseStrategy(BaseModel):
    strategyName: str
    data: dict


class Strategy(ModelBaseInfo):
    ...


class FindStrategyResult(BaseModel):
    founds: Optional[List[Strategy]]
    search_options: Optional[SearchOptions]

