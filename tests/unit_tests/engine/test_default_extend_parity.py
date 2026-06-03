"""
Sprint 7 control gate — DSL_EXTEND parity for ``default.py``.

The roadmap calls out one specific acceptance test for S7:

> Tests: extender `default.py` con una regla "bonus si es primera vez",
> comparar resultado vs. baseline.

This module replicates all 8 scenarios from
``tests/unit_tests/engine/test_default.py`` against a DSL_EXTEND wrapper
that adds a single post-rule:

    if user.measurements_count == 0:
        set_points (parent.points + 5)

For each scenario the test verifies that the wrapper's output is:
* identical to the baseline when the condition is FALSE (user has run
  the task before), and
* baseline + 5 with the same case_name when the condition is TRUE
  (first-time user).

If parity is not 100%, the gate blocks Sprint 8: an extender that can't
be expressed correctly against the most-exercised built-in means the
3-phase pipeline has a semantic gap that needs fixing before the next
sprint relies on it.
"""

from __future__ import annotations

from typing import Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.engine.default import EnhancedGamificationStrategy
from app.engine.dsl_interpreter import DslInterpreter
from app.engine.dsl_strategy import DslStrategy
from app.engine.dsl_validator import validate_ast
from app.schema.strategy_definition_schema import StrategyDefinitionRead

# Mirror of the analytics method set used by ``default.py``. Each
# scenario specifies the subset of methods it cares about; defaults of
# 0 keep the DSL's AsyncMock path from returning unawaitable values.
_ANALYTICS_METHODS = (
    "count_measurements_by_external_task_id",
    "get_user_task_measurements_count",
    "get_avg_time_between_tasks_by_user_and_game_task",
    "get_avg_time_between_tasks_for_all_users",
    "get_last_window_time_diff",
    "get_new_last_window_time_diff",
)


def _build_analytics_mocks(returns: Dict[str, int]):
    """Same factory shape used by ``test_default_dsl_parity`` —
    sync MagicMock for the Python parent, AsyncMock for the DSL
    ExecutionContext.precompute calls."""
    py_mock = MagicMock()
    dsl_mock = MagicMock()
    for method in _ANALYTICS_METHODS:
        value = returns.get(method, 0)
        getattr(py_mock, method).return_value = value
        setattr(dsl_mock, method, AsyncMock(return_value=value))
    return py_mock, dsl_mock


# Single post-rule: bonus +5 when the user has zero recorded
# measurements yet (i.e. first-time interaction with this task).
_BONUS_POST_RULE_AST = {
    "type": "program",
    "id": "extend_default_with_first_time_bonus",
    "rules": [],
    "post_rules": [
        {
            "type": "rule",
            "id": "r_first_time_bonus",
            "when": {
                "type": "compare",
                "id": "c_first_time",
                "op": "==",
                "left": {
                    "type": "field",
                    "id": "f_user_count",
                    "path": "user.measurements_count",
                },
                "right": {"type": "literal", "id": "l_zero", "value": 0},
            },
            "then": [
                {
                    "type": "set_points",
                    "id": "sp_bonus",
                    "value": {
                        "type": "arith",
                        "id": "ar_add_bonus",
                        "op": "+",
                        "left": {
                            "type": "field",
                            "id": "f_parent_points",
                            "path": "parent.points",
                        },
                        "right": {
                            "type": "literal",
                            "id": "l_bonus",
                            "value": 5,
                        },
                    },
                }
            ],
        }
    ],
}


# Same 8 scenarios as test_default_dsl_parity (which itself mirrors
# the canonical test_default.py). Plus the "is first time" flag the
# bonus rule keys on — derived from get_user_task_measurements_count.
_SCENARIOS = [
    pytest.param(
        {"count_measurements_by_external_task_id": 1},
        (1, "BasicEngagement"),
        id="basic_engagement_when_task_count_lt_2",
    ),
    pytest.param(
        {
            "count_measurements_by_external_task_id": 3,
            "get_user_task_measurements_count": 2,
            "get_avg_time_between_tasks_by_user_and_game_task": 10,
            "get_avg_time_between_tasks_for_all_users": 5,
        },
        (1, "default"),
        id="default_when_user_count_le_2",
    ),
    pytest.param(
        {
            "count_measurements_by_external_task_id": 3,
            "get_user_task_measurements_count": 3,
            "get_avg_time_between_tasks_by_user_and_game_task": 5,
            "get_avg_time_between_tasks_for_all_users": 10,
        },
        (11, "PerformanceBonus"),
        id="performance_bonus_when_user_avg_better",
    ),
    pytest.param(
        {
            "count_measurements_by_external_task_id": 3,
            "get_user_task_measurements_count": 3,
            "get_avg_time_between_tasks_by_user_and_game_task": 10,
            "get_avg_time_between_tasks_for_all_users": 5,
            "get_last_window_time_diff": 3,
            "get_new_last_window_time_diff": 5,
        },
        (3, "IndividualOverGlobal"),
        id="individual_over_global",
    ),
    pytest.param(
        {
            "count_measurements_by_external_task_id": 3,
            "get_user_task_measurements_count": 3,
            "get_avg_time_between_tasks_by_user_and_game_task": 10,
            "get_avg_time_between_tasks_for_all_users": 5,
            "get_last_window_time_diff": 2,
            "get_new_last_window_time_diff": 9,
        },
        (15, "PeakPerformerBonus"),
        id="peak_performer_bonus",
    ),
    pytest.param(
        {
            "count_measurements_by_external_task_id": 3,
            "get_user_task_measurements_count": 3,
            "get_avg_time_between_tasks_by_user_and_game_task": 10,
            "get_avg_time_between_tasks_for_all_users": 7,
            "get_last_window_time_diff": 1,
            "get_new_last_window_time_diff": 13,
        },
        (7, "GlobalAdvantageAdjustment"),
        id="global_advantage_adjustment",
    ),
    pytest.param(
        {
            "count_measurements_by_external_task_id": 3,
            "get_user_task_measurements_count": 3,
            "get_avg_time_between_tasks_by_user_and_game_task": 10,
            "get_avg_time_between_tasks_for_all_users": 5,
            "get_last_window_time_diff": 5,
            "get_new_last_window_time_diff": 3,
        },
        (8, "IndividualAdjustment"),
        id="individual_adjustment_for_negative_diff",
    ),
    pytest.param(
        {
            "count_measurements_by_external_task_id": 3,
            "get_user_task_measurements_count": 3,
            "get_avg_time_between_tasks_by_user_and_game_task": 10,
            "get_avg_time_between_tasks_for_all_users": 5,
            "get_last_window_time_diff": 5,
            "get_new_last_window_time_diff": 5,
        },
        (1, "default"),
        id="default_when_diff_is_zero",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("analytics_returns,baseline_expected", _SCENARIOS)
async def test_default_extended_with_first_time_bonus_matches_baseline_plus_bonus(
    analytics_returns,
    baseline_expected,
):
    """For every default.py scenario, the DSL_EXTEND wrapper either
    matches the baseline (user_count > 0) or returns baseline+5 with
    the same case_name (user_count == 0).

    The condition variable is the analytics method
    ``get_user_task_measurements_count`` — when 0, the post-rule fires.
    """
    validate_ast(_BONUS_POST_RULE_AST)

    py_mock, dsl_mock = _build_analytics_mocks(analytics_returns)

    # Baseline: parent built-in alone, sync MagicMock for analytics.
    baseline_parent = EnhancedGamificationStrategy()
    baseline_parent.debug = False
    baseline_parent.user_points_analytics_service = py_mock
    baseline_result = await baseline_parent.calculate_points(
        "g",
        "t",
        "u",
    )

    # Sanity: the baseline equals the canonical Sprint 5 reference.
    assert baseline_result[:2] == baseline_expected

    # DSL_EXTEND: a fresh parent instance hands its result to the DSL,
    # which inspects user.measurements_count and conditionally adds 5.
    extend_parent = EnhancedGamificationStrategy()
    extend_parent.debug = False
    extend_parent.user_points_analytics_service = py_mock

    definition = StrategyDefinitionRead(
        id="parity-test-default-extend",
        realmId=None,
        name="default_extended_bonus",
        type="DSL_EXTEND",
        parentStrategyId="default",
        astJson=_BONUS_POST_RULE_AST,
        version=1,
        status="DRAFT",
    )
    dsl_strategy = DslStrategy(
        definition=definition,
        interpreter=DslInterpreter(max_nodes=1000, max_depth=32),
        analytics_service=dsl_mock,
        parent_strategy=extend_parent,
    )
    extended_result = await dsl_strategy.calculate_points(
        externalGameId="g",
        externalTaskId="t",
        externalUserId="u",
    )

    user_count = analytics_returns.get("get_user_task_measurements_count", 0)
    expected_points = baseline_expected[0] + (5 if user_count == 0 else 0)
    expected_case_name = baseline_expected[1]

    # The case_name MUST pass through unchanged — set_points doesn't
    # touch it, so the parent's case is what the post-rule emits.
    assert extended_result[:2] == (expected_points, expected_case_name), (
        f"Parity mismatch: baseline={baseline_result[:2]} "
        f"extended={extended_result[:2]} "
        f"expected=({expected_points}, {expected_case_name})"
    )
