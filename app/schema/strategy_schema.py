from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.schema.base_schema import ModelBaseInfo, SearchOptions


class Strategy(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    version: str
    variables: Dict[str, int]


#############################################################################

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
