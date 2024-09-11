from datetime import datetime
from uuid import uuid4

from app.schema.strategy_schema import (BaseStrategy, DataStrategy, RuleBase,
                                        StaticVariables, Strategy)


def test_strategy():
    """
    Test the Strategy model.

    The Strategy model is used for representing a strategy.

    The model has the following attributes:
    - id (str): Strategy ID
    - name (Optional[str]): Strategy name
    - description (Optional[str]): Strategy description
    - version (str): Strategy version
    - variables (Dict[str, int]): Strategy variables
    """
    data = {
        "id": "strategy123",
        "name": "Test Strategy",
        "description": "A test strategy",
        "version": "1.0",
        "variables": {"var1": 10, "var2": 20},
    }
    strategy = Strategy(**data)
    assert strategy.id == data["id"]
    assert strategy.name == data["name"]
    assert strategy.description == data["description"]
    assert strategy.version == data["version"]
    assert strategy.variables == data["variables"]


def test_rule_base():
    """
    Test the RuleBase model.

    The RuleBase model is used for representing a rule.

    The model has the following attributes:
    - name (str): Rule name
    - description (str): Rule description
    - conditions (List[str]): List of conditions
    - reward (str): Reward
    - priority (int): Priority
    """
    data = {
        "name": "Test Rule",
        "description": "A test rule",
        "conditions": ["cond1", "cond2"],
        "reward": "reward",
        "priority": 1,
    }
    rule = RuleBase(**data)
    assert rule.name == data["name"]
    assert rule.description == data["description"]
    assert rule.conditions == data["conditions"]
    assert rule.reward == data["reward"]
    assert rule.priority == data["priority"]


def test_static_variables():
    """
    Test the StaticVariables model.

    The StaticVariables model is used for representing static variables.

    The model has the following attributes:

    - BASIC_POINTS (int): Basic points
    - BONUS_FACTOR (float): Bonus factor
    """
    data = {"BASIC_POINTS": 100, "BONUS_FACTOR": 1.5}
    static_vars = StaticVariables(**data)
    assert static_vars.BASIC_POINTS == data["BASIC_POINTS"]
    assert static_vars.BONUS_FACTOR == data["BONUS_FACTOR"]


def test_data_strategy():
    """
    Test the DataStrategy model.

    The DataStrategy model is used for representing a data strategy.

    The model has the following attributes:
    - label (str): Label
    - description (str): Description
    - tags (List[str]): List of tags
    - static_variables (StaticVariables): Static variables
    - rules (List[RuleBase]): List of rules
    """
    static_vars_data = {"BASIC_POINTS": 100, "BONUS_FACTOR": 1.5}
    rules_data = [
        {
            "name": "Test Rule 1",
            "description": "A test rule 1",
            "conditions": ["cond1", "cond2"],
            "reward": "reward1",
            "priority": 1,
        },
        {
            "name": "Test Rule 2",
            "description": "A test rule 2",
            "conditions": ["cond3", "cond4"],
            "reward": "reward2",
            "priority": 2,
        },
    ]
    data = {
        "label": "Test Data Strategy",
        "description": "A test data strategy",
        "tags": ["tag1", "tag2"],
        "static_variables": StaticVariables(**static_vars_data),
        "rules": [RuleBase(**rule) for rule in rules_data],
    }
    data_strategy = DataStrategy(**data)
    assert data_strategy.label == data["label"]
    assert data_strategy.description == data["description"]
    assert data_strategy.tags == data["tags"]
    assert data_strategy.static_variables == data["static_variables"]
    assert data_strategy.rules == data["rules"]


def test_base_strategy():
    """
    Test the BaseStrategy model.

    The BaseStrategy model is used as a base model for a strategy.

    The model has the following attributes:
    - strategyName (str): Strategy name
    - data (DataStrategy): Data strategy
    """
    static_vars_data = {"BASIC_POINTS": 100, "BONUS_FACTOR": 1.5}
    rules_data = [
        {
            "name": "Test Rule 1",
            "description": "A test rule 1",
            "conditions": ["cond1", "cond2"],
            "reward": "reward1",
            "priority": 1,
        },
        {
            "name": "Test Rule 2",
            "description": "A test rule 2",
            "conditions": ["cond3", "cond4"],
            "reward": "reward2",
            "priority": 2,
        },
    ]
    data_strategy = {
        "label": "Test Data Strategy",
        "description": "A test data strategy",
        "tags": ["tag1", "tag2"],
        "static_variables": StaticVariables(**static_vars_data),
        "rules": [RuleBase(**rule) for rule in rules_data],
    }
    data = {
        "id": uuid4(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "strategyName": "Test Strategy",
        "data": DataStrategy(**data_strategy),
    }
    base_strategy = BaseStrategy(**data)
    assert base_strategy.strategyName == data["strategyName"]
    assert base_strategy.data == data["data"]
