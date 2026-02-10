from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schema.base_schema import ModelBaseInfo


class Strategy(BaseModel):
    """
    Public strategy definition metadata.

    Attributes:
        id (str): Unique strategy identifier.
        name (Optional[str]): Human-readable strategy name.
        description (Optional[str]): Strategy description and intent.
        version (str): Semantic or internal strategy version.
        variables (Dict[str, Any]): Runtime variables consumed by the strategy.
        hash_version (Optional[str]): Hash fingerprint of strategy content/version.
    """

    id: str = Field(
        ...,
        description="Unique strategy identifier.",
        example="default",
    )
    name: Optional[str] = Field(
        default=None,
        description="Human-readable strategy name.",
        example="Default Adaptive Strategy",
    )
    description: Optional[str] = Field(
        default=None,
        description="Business and scoring intent of the strategy.",
        example="Balanced adaptive scoring based on engagement and performance.",
    )
    version: str = Field(
        ...,
        description="Version string of the strategy definition.",
        example="1.0.0",
    )
    variables: Dict[str, Any] = Field(
        ...,
        description="Configurable variables used by the strategy engine.",
        example={"variable_basic_points": 10, "bonus_factor": 1.2},
    )
    hash_version: Optional[str] = Field(
        default=None,
        description="Hash or fingerprint representing strategy content/version.",
        example="9bcf1a8f3b2d4e5c7a8f9e0d1b2c3d4e",
    )


class RuleBase(BaseModel):
    """
    Rule definition used inside a strategy.

    Attributes:
        name (str): Rule name.
        description (str): Rule explanation.
        conditions (List[str]): List of condition expressions.
        reward (str): Reward/action to apply when rule matches.
        priority (int): Rule execution priority.
    """

    name: str = Field(
        ...,
        description="Rule name.",
        example="Performance Bonus",
    )
    description: str = Field(
        ...,
        description="Description of the rule behavior.",
        example="Awards bonus points when completion time is below threshold.",
    )
    conditions: List[str] = Field(
        ...,
        description="List of condition expressions evaluated for this rule.",
        example=["duration_minutes < 5", "task_completed == true"],
    )
    reward: str = Field(
        ...,
        description="Reward action applied when all conditions match.",
        example="add_bonus_points",
    )
    priority: int = Field(
        ...,
        description="Execution priority. Lower value means higher priority.",
        example=1,
    )


class StaticVariables(BaseModel):
    """
    Static tuning constants used by strategy rules.

    Attributes:
        BASIC_POINTS (int): Baseline points for a standard action.
        BONUS_FACTOR (float): Multiplicative bonus factor.
    """

    BASIC_POINTS: int = Field(
        ...,
        description="Base points awarded for standard qualifying actions.",
        example=10,
    )
    BONUS_FACTOR: float = Field(
        ...,
        description="Multiplier applied when bonus conditions are satisfied.",
        example=1.5,
    )


class DataStrategy(BaseModel):
    """
    Full strategy payload including labels, tags, constants, and rules.

    Attributes:
        label (str): Short strategy label.
        description (str): Strategy description.
        tags (List[str]): Classification tags for discovery/filtering.
        static_variables (StaticVariables): Global static variables.
        rules (List[RuleBase]): Ordered list of strategy rules.
    """

    label: str = Field(
        ...,
        description="Short strategy label.",
        example="default_adaptive",
    )
    description: str = Field(
        ...,
        description="Detailed strategy description.",
        example="Adaptive strategy balancing consistency and performance metrics.",
    )
    tags: List[str] = Field(
        ...,
        description="Tags used for strategy categorization and filtering.",
        example=["adaptive", "engagement", "baseline"],
    )
    static_variables: StaticVariables = Field(
        ...,
        description="Static constants used by rules.",
    )
    rules: List[RuleBase] = Field(
        ...,
        description="Ordered ruleset applied by the strategy engine.",
    )


class BaseStrategy(ModelBaseInfo):
    """
    Persisted strategy entity returned by strategy endpoints.

    Attributes:
        strategyName (str): Strategy name.
        data (DataStrategy): Strategy data payload.
    """

    strategyName: str = Field(
        ...,
        description="Name of the persisted strategy entity.",
        example="Default Strategy",
    )
    data: DataStrategy = Field(
        ...,
        description="Structured strategy data including tags, constants, and rules.",
    )
