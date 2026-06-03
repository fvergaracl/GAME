"""
Sprint 6 parity test — gate that ``constantEffortStrategy`` can be
expressed as a DSL AST that produces identical outputs to the Python
implementation.

This is the second strategy migrated to the DSL (after ``default.py``
in Sprint 5). It exercises the AST extensions introduced in Sprint 6:

* ``NODE_FUNC_CALL`` for the unary ``int`` cast and the ternary ``clamp``
  expression that mirror ``min(max(int(normalized), 1), variable_max_points)``
  on ``constantEffortStrategy.py:53``.
* The ``user.recent_measurements_count`` field resolver that wraps the
  asynchronous ``get_user_task_measurements_count_the_last_seconds``
  analytics call (with the strategy's default 5-minute window hardcoded
  in the resolver — see the Sprint 6 plan §A.1.2 for why).

Note on parity scope: the Python helper computes
``normalized = (consistent_effort_count / 100) * 100``, which always
simplifies to ``consistent_effort_count`` for the default
``variable_max_points = 100``. The DSL AST mirrors the same arithmetic
shape so that future tweaks to the divisor / multiplier in the Python
side would force the AST to be updated in lockstep.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.engine.constantEffortStrategy import ConstantEffortStrategy
from app.engine.dsl_interpreter import DslInterpreter
from app.engine.dsl_strategy import DslStrategy
from app.schema.strategy_definition_schema import StrategyDefinitionRead

_AST_PATH = (
    Path(__file__).resolve().parents[3]
    / "app"
    / "engine"
    / "dsl_templates"
    / "constant_effort_v0_0_1.json"
)
_AST: Dict = json.loads(_AST_PATH.read_text(encoding="utf-8"))


# Same factory shape as ``test_default_dsl_parity.py``: a single dict of
# analytics return values feeds both Python (sync MagicMock) and DSL
# (AsyncMock) variants so we can never desync them by accident.
_ANALYTICS_METHODS = ("get_user_task_measurements_count_the_last_seconds",)


def _build_analytics_mocks(returns: Dict[str, int]):
    py_mock = MagicMock()
    dsl_mock = MagicMock()
    for method in _ANALYTICS_METHODS:
        value = returns.get(method, 0)
        getattr(py_mock, method).return_value = value
        setattr(dsl_mock, method, AsyncMock(return_value=value))
    return py_mock, dsl_mock


def _build_dsl_strategy(analytics_mock: MagicMock) -> DslStrategy:
    definition = StrategyDefinitionRead(
        id="parity-test-constant-effort",
        realmId=None,
        name="constant_effort_parity",
        type="DSL_FULL",
        astJson=_AST,
        version=1,
        status="PUBLISHED",
    )
    interpreter = DslInterpreter(max_nodes=1000, max_depth=32)
    return DslStrategy(
        definition=definition,
        interpreter=interpreter,
        analytics_service=analytics_mock,
    )


# Scenario rationale: each row picks a value of
# ``get_user_task_measurements_count_the_last_seconds`` (let's call it
# ``n``). Python branches at ``n > 0``; if true it computes
# ``clamp(int((n+1)/100 * 100), 1, 100)``; otherwise returns BasicReward.
# Both implementations must agree on the (points, case_name) pair.
_SCENARIOS = [
    pytest.param(
        {"get_user_task_measurements_count_the_last_seconds": 0},
        (1, "BasicReward"),
        id="basic_reward_when_no_recent_measurements",
    ),
    pytest.param(
        {"get_user_task_measurements_count_the_last_seconds": 1},
        (2, "ConstantEffortReward"),
        id="constant_effort_minimum_when_count_is_one",
    ),
    pytest.param(
        {"get_user_task_measurements_count_the_last_seconds": 4},
        (5, "ConstantEffortReward"),
        id="constant_effort_low_when_count_is_four",
    ),
    pytest.param(
        {"get_user_task_measurements_count_the_last_seconds": 99},
        (100, "ConstantEffortReward"),
        id="constant_effort_at_ceiling_when_count_is_ninety_nine",
    ),
    pytest.param(
        # clamp ceiling: count=150 → (151/100)*100=151 → int(151)=151 →
        # clamp(151, 1, 100) = 100. Verifies the clamp's hi bound fires.
        {"get_user_task_measurements_count_the_last_seconds": 150},
        (100, "ConstantEffortReward"),
        id="constant_effort_clamps_above_max_points",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("analytics_returns,expected", _SCENARIOS)
async def test_dsl_constant_effort_matches_python(analytics_returns, expected):
    """Each branch of ConstantEffortStrategy.calculate_points must yield
    identical (points, case_name) when the DSL version is fed the same
    inputs."""
    py_mock, dsl_mock = _build_analytics_mocks(analytics_returns)

    py_strategy = ConstantEffortStrategy()
    py_strategy.debug = False
    py_strategy.user_points_analytics_service = py_mock
    py_result = await py_strategy.calculate_points("g", "t", "u")

    dsl_strategy = _build_dsl_strategy(dsl_mock)
    dsl_result = await dsl_strategy.calculate_points(
        externalGameId="g",
        externalTaskId="t",
        externalUserId="u",
    )

    # Same slicing rationale as test_default_dsl_parity.py: DslStrategy
    # returns a 3-tuple only when callback_data is non-empty; the
    # constant_effort AST never writes callback_data.
    assert dsl_result[:2] == py_result[:2], (
        f"Parity mismatch: python={py_result} dsl={dsl_result} " f"expected={expected}"
    )
    assert py_result[:2] == expected
    assert dsl_result[:2] == expected


@pytest.mark.asyncio
async def test_constant_effort_ast_template_is_structurally_valid():
    """Defence in depth: re-validate the persisted AST so an accidental
    edit to ``constant_effort_v0_0_1.json`` can't ship a broken template."""
    from app.engine.dsl_validator import validate_ast

    validate_ast(_AST)
