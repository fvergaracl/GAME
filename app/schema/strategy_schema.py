from typing import Dict, List, Optional
from pydantic import BaseModel
from app.schema.base_schema import ModelBaseInfo


class Strategy(BaseModel):
    """
    Model for a strategy

    Attributes:
        id (str): Strategy ID
        name (Optional[str]): Strategy name
        description (Optional[str]): Strategy description
        version (str): Strategy version
        variables (Dict[str, int]): Strategy variables
    """
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    version: str
    variables: Dict[str, int]


class RuleBase(BaseModel):
    """
    Model for a rule

    Attributes:
        name (str): Rule name
        description (str): Rule description
        conditions (List[str]): List of conditions
        reward (str): Reward
        priority (int): Priority
    """
    name: str
    description: str
    conditions: List[str]
    reward: str
    priority: int


class StaticVariables(BaseModel):
    """
    Model for static variables

    Attributes:
        BASIC_POINTS (int): Basic points
        BONUS_FACTOR (float): Bonus factor
    """
    BASIC_POINTS: int
    BONUS_FACTOR: float


class DataStrategy(BaseModel):
    """
    Model for data strategy

    Attributes:
        label (str): Label
        description (str): Description
        tags (List[str]): List of tags
        static_variables (StaticVariables): Static variables
        rules (List[RuleBase]): List of rules
    """
    label: str
    description: str
    tags: List[str]
    static_variables: StaticVariables
    rules: List[RuleBase]


class BaseStrategy(ModelBaseInfo):
    """
    Base model for a strategy

    Attributes:
        strategyName (str): Strategy name
        data (DataStrategy): Data strategy
    """
    strategyName: str
    data: DataStrategy
