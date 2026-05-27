"""
Parity tests for Sprint 5 — gate that blocks Sprint 6.

The DSL infrastructure built in Sprint 4 ships with no proof that the AST
grammar can actually express a real production strategy. This module is
that proof: it loads ``app/engine/dsl_templates/default_v0_0_2.json`` (the
JSON-AST rewrite of ``app/engine/default.py``) and runs both
implementations against the eight scenarios already covered by
``tests/unit_tests/engine/test_default.py``.

Every scenario must agree on ``(points, case_name)`` — if even one
diverges, ``test_default.py`` and the parity test cannot both be true and
S6 is blocked by the roadmap's control gate.

Why two mock shapes?  ``EnhancedGamificationStrategy`` calls the analytics
methods synchronously (``service.method(...)``); ``DslStrategy`` runs them
through ``ExecutionContext.build_for_ast`` which awaits each one. A single
analytics service object cannot satisfy both call styles. ``build_analytics_mocks``
keeps the two in lockstep by reading the same scenario dict and producing
a ``MagicMock`` for Python plus an ``AsyncMock``-decorated ``MagicMock``
for the DSL.

Defaulting unspecified analytics to ``0``: the rule ordering in the AST
short-circuits long before unused paths matter (scenario 1 matches rule
1 on ``task.measurements_count < 2``, so the value of every other
analytic is irrelevant). Defaulting to ``0`` is purely defensive so that
the DSL's ``await`` never lands on an unconfigured MagicMock attribute.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.engine.default import EnhancedGamificationStrategy
from app.engine.dsl_interpreter import DslInterpreter
from app.engine.dsl_strategy import DslStrategy
from app.schema.strategy_definition_schema import StrategyDefinitionRead


_AST_PATH = (
    Path(__file__).resolve().parents[3]
    / "app"
    / "engine"
    / "dsl_templates"
    / "default_v0_0_2.json"
)
_AST: Dict = json.loads(_AST_PATH.read_text(encoding="utf-8"))


_ANALYTICS_METHODS = (
    "count_measurements_by_external_task_id",
    "get_user_task_measurements_count",
    "get_avg_time_between_tasks_by_user_and_game_task",
    "get_avg_time_between_tasks_for_all_users",
    "get_last_window_time_diff",
    "get_new_last_window_time_diff",
)


def _build_analytics_mocks(returns: Dict[str, float]):
    """
    Build two mocks that resolve every analytic to the same value: a sync
    ``MagicMock`` for the Python strategy and an ``AsyncMock``-decorated
    ``MagicMock`` for the DSL strategy. Unspecified methods default to 0.
    """
    py_mock = MagicMock()
    dsl_mock = MagicMock()
    for method in _ANALYTICS_METHODS:
        value = returns.get(method, 0)
        getattr(py_mock, method).return_value = value
        setattr(dsl_mock, method, AsyncMock(return_value=value))
    return py_mock, dsl_mock


def _build_dsl_strategy(analytics_mock: MagicMock) -> DslStrategy:
    """Construct a DslStrategy directly from the on-disk AST, no DB round-trip."""
    definition = StrategyDefinitionRead(
        id="parity-test-default",
        realmId=None,
        name="default_parity",
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


# Scenarios mirror tests/unit_tests/engine/test_default.py one-for-one.
# The dict shape is identical to what _set_shared_values would push to
# the analytics mock; missing keys default to 0 in _build_analytics_mocks.
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
@pytest.mark.parametrize("analytics_returns,expected", _SCENARIOS)
async def test_dsl_default_matches_python_default(analytics_returns, expected):
    """Each branch of EnhancedGamificationStrategy must yield identical
    ``(points, case_name)`` when the DSL version is fed the same inputs."""
    py_mock, dsl_mock = _build_analytics_mocks(analytics_returns)

    py_strategy = EnhancedGamificationStrategy()
    py_strategy.debug = False
    py_strategy.user_points_analytics_service = py_mock
    py_result = await py_strategy.calculate_points("game_id", "task_id", "user_id")

    dsl_strategy = _build_dsl_strategy(dsl_mock)
    dsl_result = await dsl_strategy.calculate_points(
        externalGameId="game_id",
        externalTaskId="task_id",
        externalUserId="user_id",
    )

    # Trim to (points, case_name): DslStrategy returns a 3-tuple only when
    # callback_data is non-empty; the default AST never writes callback_data.
    assert dsl_result[:2] == py_result[:2], (
        f"Parity mismatch: python={py_result} dsl={dsl_result} "
        f"expected={expected}"
    )
    # Sanity: both implementations match the roadmap's tabulated expectations.
    assert py_result[:2] == expected
    assert dsl_result[:2] == expected


@pytest.mark.asyncio
async def test_ast_template_is_structurally_valid():
    """Defence in depth: re-validate the persisted AST so an accidental
    edit to ``default_v0_0_2.json`` can't ship a broken template."""
    from app.engine.dsl_validator import validate_ast

    # Mutates only by filling auto-ids; the template already has ids so
    # this is a pure validity check.
    validate_ast(_AST)
