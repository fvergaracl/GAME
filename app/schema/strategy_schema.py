from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.schema.base_schema import ModelBaseInfo, SearchOptions
"""
{
    "label": "Default",
    "description": "Default rule",
    "tags": [
        "default"
    ],
    "static_variables": {
        "BASIC_POINTS": 100,
        "BONUS_FACTOR": 1.5
    },
    "rules": [
        {
            "name": "Default",
            "description": "Default rule",
            "conditions": [],
            "reward": "@BASIC_POINTS",
            "priority": 1
        },
        {
            "name": "First_action_game",
            "description": "First action in game",
            "conditions": [
                "@AVG_POINTS_GAME_BY_USER == 0"
            ],
            "reward": "@BASIC_POINTS * @BONUS_FACTOR"
        },
        {
            "name": "First_action_task",
            "description": "First action in task",
            "conditions": [
                "@AVG_POINTS_TASK_BY_USER == 0"
            ],
            "reward": "@BASIC_POINTS * @BONUS_FACTOR"
        }
    ]
}
"""


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


class BaseStrategy(BaseModel):
    strategyName: str
    data: DataStrategy


class Strategy(ModelBaseInfo):
    data: Dict[str, Any]


class FindAllStrategyResult(BaseModel):
    founds: Optional[List[BaseStrategy]]
    search_options: Optional[SearchOptions]


class FindStrategyResult(Strategy):
    ...


class CreateStrategyPost(BaseStrategy):
    ...


class CreateStrategyResult(Strategy):
    ...
