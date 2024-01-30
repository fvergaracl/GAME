from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.schema.base_schema import ModelBaseInfo, SearchOptions


class RuleBase(BaseModel):
    name: str
    description: str
    conditions: List[str]
    reward: str
    priority: int


class StaticVariables(BaseModel):
    BASIC_POINTS: int
    BONUS_FACTOR: float


class DataStrategy(BaseModel):
    label: str
    description: str
    tags: List[str]
    static_variables: StaticVariables
    rules: List[RuleBase]


class BaseStrategy(ModelBaseInfo):
    strategyName: str
    data: DataStrategy


class Strategy(ModelBaseInfo):
    data: Dict[str, Any]


class FindAllStrategyResult(BaseModel):
    items: Optional[List[BaseStrategy]]
    search_options: Optional[SearchOptions]


class FindStrategyResult(Strategy):
    ...


class CreateStrategyPost(BaseStrategy):
    ...


class CreateStrategyResult(Strategy):
    ...
