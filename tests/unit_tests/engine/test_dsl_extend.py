"""
Sprint 7 - DSL_EXTEND end-to-end tests for the 3-phase pipeline.

This module exercises ``DslStrategy`` with a ``parent_strategy``
injected (the path that ``StrategyService.get_strategy_instance`` builds
when a custom strategy row carries ``type=DSL_EXTEND``). The parent is
a tiny mock that lets each test pin a deterministic
``(points, case_name, callback_data)`` tuple and assert what data the
parent saw - which is how we prove that pre-rule ``set_data`` actually
reaches the parent built-in.

Companion module: ``test_default_extend_parity.py`` (S7 control gate
"default + bonus si es primera vez").
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import DslValidationError
from app.engine.base_strategy import BaseStrategy
from app.engine.dsl_interpreter import DslInterpreter
from app.engine.dsl_strategy import DslStrategy
from app.engine.dsl_validator import validate_ast
from app.schema.strategy_definition_schema import StrategyDefinitionRead

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


class _MockParent(BaseStrategy):
    """Minimal parent built-in for DSL_EXTEND tests.

    - Captures the data dict it was invoked with so tests can assert
      pre-rule mutations reached it.
    - Returns a configurable ``(points, case_name, callback_data)``
      tuple. callback_data only appears in the tuple when non-empty,
      mirroring real built-ins like ``EnhancedGamificationStrategy``.
    """

    def __init__(
        self,
        *,
        points: int = 5,
        case_name: str = "ParentResult",
        callback_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            strategy_name="MockParent",
            strategy_description="Test double for DSL_EXTEND.",
            strategy_name_slug="mock_parent",
            strategy_version="0.0.1",
            variable_basic_points=1,
            variable_bonus_points=1,
        )
        self.variable_basic_points = points
        self.variable_bonus_points = 2
        self._configured_points = points
        self._configured_case_name = case_name
        self._configured_callback = callback_data or {}
        self.last_call_args: Optional[Dict[str, Any]] = None

    async def calculate_points(  # noqa: D401
        self,
        externalGameId=None,
        externalTaskId=None,
        externalUserId=None,
        data=None,
    ):
        # Snapshot the inputs so the test can assert pre-rule mutations.
        self.last_call_args = {
            "externalGameId": externalGameId,
            "externalTaskId": externalTaskId,
            "externalUserId": externalUserId,
            "data": dict(data or {}),
        }
        # Use ``variable_basic_points`` so the parent_variables test can
        # exercise the override path through set_variables.
        if self._configured_callback:
            return (
                self.variable_basic_points,
                self._configured_case_name,
                dict(self._configured_callback),
            )
        return (self.variable_basic_points, self._configured_case_name)


def _build_strategy(
    ast: Dict[str, Any],
    parent: BaseStrategy,
    *,
    analytics_returns: Optional[Dict[str, Any]] = None,
) -> DslStrategy:
    """Wire a DslStrategy with the AST under test and a mock parent.

    Validates the AST up front so a test exercising the runtime never
    gets a confusing failure from an unrelated grammar bug."""
    validate_ast(ast)

    analytics_mock = MagicMock()
    for method, value in (analytics_returns or {}).items():
        setattr(analytics_mock, method, AsyncMock(return_value=value))

    definition = StrategyDefinitionRead(
        id="test-extend",
        realmId=None,
        name="extend_test",
        type="DSL_EXTEND",
        parentStrategyId="mock_parent",
        astJson=ast,
        version=1,
        status="DRAFT",
    )
    interpreter = DslInterpreter(max_nodes=1000, max_depth=32)
    return DslStrategy(
        definition=definition,
        interpreter=interpreter,
        analytics_service=analytics_mock,
        parent_strategy=parent,
    )


def _always_true_when() -> Dict[str, Any]:
    """Reusable always-true condition (literal True as bare expression)."""
    return {"type": "literal", "id": "lt", "value": True}


# ---------------------------------------------------------------------------
# Pre-rules
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pre_rule_mutates_data_passed_to_parent():
    """``set_data`` in pre_rules writes into the dict that the parent
    built-in receives - proves the pre→parent handoff works."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [],
        "pre_rules": [
            {
                "type": "rule",
                "id": "pr1",
                "when": _always_true_when(),
                "then": [
                    {
                        "type": "set_data",
                        "id": "sd1",
                        "key": "is_first_time",
                        "value": {"type": "literal", "id": "lv", "value": True},
                    }
                ],
            }
        ],
    }
    parent = _MockParent(points=7, case_name="Welcomed")
    strategy = _build_strategy(ast, parent)

    result = await strategy.calculate_points("g", "t", "u", data={"foo": "bar"})

    assert parent.last_call_args is not None
    assert parent.last_call_args["data"]["is_first_time"] is True
    # The original data is preserved alongside the mutation.
    assert parent.last_call_args["data"]["foo"] == "bar"
    # Parent's output flows through unchanged when no post_rules exist.
    assert result == (7, "Welcomed")


@pytest.mark.asyncio
async def test_pre_rule_veto_skips_parent_and_post():
    """A pre-rule ``veto`` short-circuits both the parent call and the
    post_rules - the final result is (0, veto_case_name)."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [],
        "pre_rules": [
            {
                "type": "rule",
                "id": "pr1",
                "when": _always_true_when(),
                "then": [
                    {
                        "type": "veto",
                        "id": "v1",
                        "case_name": "TooEarly",
                    }
                ],
            }
        ],
        "post_rules": [
            # This post-rule should NEVER fire (the veto kills the
            # pipeline before phase 3).
            {
                "type": "rule",
                "id": "post1",
                "when": _always_true_when(),
                "then": [
                    {
                        "type": "set_points",
                        "id": "sp",
                        "value": {"type": "literal", "id": "lv", "value": 999},
                    }
                ],
            }
        ],
    }
    parent = _MockParent(points=42, case_name="ShouldNotAppear")
    strategy = _build_strategy(ast, parent)

    result = await strategy.calculate_points("g", "t", "u")

    assert result == (0, "TooEarly")
    assert parent.last_call_args is None  # parent was never invoked


@pytest.mark.asyncio
async def test_pre_rule_with_false_condition_does_not_mutate():
    """A pre-rule whose ``when`` is false should not run its body -
    the parent sees the original data untouched."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [],
        "pre_rules": [
            {
                "type": "rule",
                "id": "pr1",
                "when": {"type": "literal", "id": "lt", "value": False},
                "then": [
                    {
                        "type": "set_data",
                        "id": "sd",
                        "key": "should_not_appear",
                        "value": {"type": "literal", "id": "lv", "value": 1},
                    }
                ],
            }
        ],
    }
    parent = _MockParent(points=3, case_name="Untouched")
    strategy = _build_strategy(ast, parent)

    result = await strategy.calculate_points("g", "t", "u", data={"orig": True})

    assert "should_not_appear" not in parent.last_call_args["data"]
    assert parent.last_call_args["data"]["orig"] is True
    assert result == (3, "Untouched")


# ---------------------------------------------------------------------------
# Post-rules
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_rule_set_points_overrides_parent_using_arith():
    """A post-rule can read ``parent.points`` and overwrite it via
    arithmetic - this is the canonical "multiply parent's reward"
    workflow."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [],
        "post_rules": [
            {
                "type": "rule",
                "id": "post1",
                "when": _always_true_when(),
                "then": [
                    {
                        "type": "set_points",
                        "id": "sp",
                        "value": {
                            "type": "arith",
                            "id": "ar",
                            "op": "*",
                            "left": {
                                "type": "field",
                                "id": "fp",
                                "path": "parent.points",
                            },
                            "right": {
                                "type": "literal",
                                "id": "lr",
                                "value": 2,
                            },
                        },
                    }
                ],
            }
        ],
    }
    parent = _MockParent(points=5, case_name="Doubled")
    strategy = _build_strategy(ast, parent)

    result = await strategy.calculate_points("g", "t", "u")

    assert result == (10, "Doubled")


@pytest.mark.asyncio
async def test_post_rule_set_case_name_overrides_parent():
    """A post-rule can rewrite the case_name (e.g. brand a parent's
    PerformanceBonus as something realm-specific)."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [],
        "post_rules": [
            {
                "type": "rule",
                "id": "post1",
                "when": _always_true_when(),
                "then": [
                    {
                        "type": "set_case_name",
                        "id": "scn",
                        "value": {
                            "type": "literal",
                            "id": "lv",
                            "value": "EnhancedReward",
                        },
                    }
                ],
            }
        ],
    }
    parent = _MockParent(points=5, case_name="ParentCase")
    strategy = _build_strategy(ast, parent)

    result = await strategy.calculate_points("g", "t", "u")

    # Points unchanged, case_name overridden.
    assert result == (5, "EnhancedReward")


@pytest.mark.asyncio
async def test_post_rule_set_callback_data_accumulates_over_parent():
    """Parent's callback_data passes through, then post-rule appends -
    the final callback_data is the merge (post-rule key wins on collision
    because the last write wins)."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [],
        "post_rules": [
            {
                "type": "rule",
                "id": "post1",
                "when": _always_true_when(),
                "then": [
                    {
                        "type": "set_callback_data",
                        "id": "scd",
                        "key": "extended_by_dsl",
                        "value": {
                            "type": "literal",
                            "id": "lv",
                            "value": True,
                        },
                    }
                ],
            }
        ],
    }
    parent = _MockParent(
        points=3,
        case_name="ParentCase",
        callback_data={"parent_marker": "from_parent"},
    )
    strategy = _build_strategy(ast, parent)

    result = await strategy.calculate_points("g", "t", "u")

    # 3-tuple because callback_data is non-empty.
    assert len(result) == 3
    points, case_name, cb = result
    assert points == 3
    assert case_name == "ParentCase"
    assert cb["parent_marker"] == "from_parent"
    assert cb["extended_by_dsl"] is True


@pytest.mark.asyncio
async def test_post_rule_branches_on_parent_case_name():
    """Reading ``parent.case_name`` lets the designer route post-actions
    by which case the parent emitted - a critical extensibility hook."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [],
        "post_rules": [
            {
                "type": "rule",
                "id": "post1",
                "when": {
                    "type": "compare",
                    "id": "c",
                    "op": "==",
                    "left": {
                        "type": "field",
                        "id": "fp",
                        "path": "parent.case_name",
                    },
                    "right": {
                        "type": "literal",
                        "id": "lr",
                        "value": "BasicEngagement",
                    },
                },
                "then": [
                    {
                        "type": "set_points",
                        "id": "sp",
                        "value": {"type": "literal", "id": "lv", "value": 99},
                    }
                ],
            }
        ],
    }
    # Branch hit: parent emits BasicEngagement → post overwrites to 99.
    strategy = _build_strategy(ast, _MockParent(points=1, case_name="BasicEngagement"))
    assert await strategy.calculate_points("g", "t", "u") == (99, "BasicEngagement")

    # Branch miss: parent emits something else → result passes through.
    strategy = _build_strategy(ast, _MockParent(points=11, case_name="OtherCase"))
    assert await strategy.calculate_points("g", "t", "u") == (11, "OtherCase")


# ---------------------------------------------------------------------------
# parent_variables
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parent_variables_override_applied_to_copy():
    """``parent_variables`` overrides the parent's ``variable_*`` BEFORE
    calculate_points runs - and only on a copy, so the registry
    singleton is unaffected for the next request."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [],
        "parent_variables": {
            "variable_basic_points": 77,
        },
    }
    parent = _MockParent(points=5, case_name="OverridePath")
    # Sanity: parent's basic_points starts at 5 (the configured value).
    assert parent.variable_basic_points == 5

    strategy = _build_strategy(ast, parent)
    result = await strategy.calculate_points("g", "t", "u")

    # Mock parent returns ``self.variable_basic_points`` as points, so
    # the override flows through end to end.
    assert result == (77, "OverridePath")
    # Original singleton is unchanged after the run.
    assert parent.variable_basic_points == 5


def test_parent_variables_rejects_non_variable_key():
    """The validator refuses keys that don't follow the ``variable_*``
    convention - pre-empts injection of arbitrary parent attributes."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [],
        "parent_variables": {"debug": True},  # not "variable_..."
    }
    with pytest.raises(
        DslValidationError, match="must be a string starting with 'variable_'"
    ):
        validate_ast(ast)


def test_parent_variables_rejects_non_scalar_value():
    """``parent_variables`` values must be JSON scalars - no nested
    objects or arrays (they'd not round-trip through set_variables
    predictably)."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [],
        "parent_variables": {"variable_basic_points": [1, 2, 3]},
    }
    with pytest.raises(DslValidationError, match="must be a JSON scalar"):
        validate_ast(ast)


# ---------------------------------------------------------------------------
# Validator context enforcement
# ---------------------------------------------------------------------------


def test_validator_rejects_field_parent_points_in_main_rule():
    """``parent.points`` only makes sense in post_rules - using it in
    a main rule would read uninitialised state."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r",
                "when": {
                    "type": "compare",
                    "id": "c",
                    "op": ">",
                    "left": {
                        "type": "field",
                        "id": "fp",
                        "path": "parent.points",
                    },
                    "right": {"type": "literal", "id": "l", "value": 0},
                },
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a",
                        "value": {"type": "literal", "id": "lv", "value": 1},
                        "case_name": "x",
                    }
                ],
            }
        ],
    }
    with pytest.raises(DslValidationError, match="only available inside post_rules"):
        validate_ast(ast)


def test_validator_rejects_set_data_in_main_rule():
    """``set_data`` is pre-only - using it in a main rule is a designer
    bug worth catching at validation time."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r",
                "when": _always_true_when(),
                "then": [
                    {
                        "type": "set_data",
                        "id": "sd",
                        "key": "x",
                        "value": {"type": "literal", "id": "lv", "value": 1},
                    }
                ],
            }
        ],
    }
    with pytest.raises(DslValidationError, match="not allowed inside 'rule'"):
        validate_ast(ast)


def test_validator_rejects_set_points_in_pre_rule():
    """``set_points`` is post-only - pre-rules don't have meaningful
    points to set yet."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [],
        "pre_rules": [
            {
                "type": "rule",
                "id": "pr",
                "when": _always_true_when(),
                "then": [
                    {
                        "type": "set_points",
                        "id": "sp",
                        "value": {"type": "literal", "id": "lv", "value": 5},
                    }
                ],
            }
        ],
    }
    with pytest.raises(DslValidationError, match="not allowed inside 'pre'"):
        validate_ast(ast)


def test_validator_accepts_field_parent_points_in_post_rule():
    """Happy path counterpart to the rejection tests - confirms the
    field path IS valid in post_rules context."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [],
        "post_rules": [
            {
                "type": "rule",
                "id": "post1",
                "when": _always_true_when(),
                "then": [
                    {
                        "type": "set_points",
                        "id": "sp",
                        "value": {
                            "type": "field",
                            "id": "fp",
                            "path": "parent.points",
                        },
                    }
                ],
            }
        ],
    }
    validate_ast(ast)  # no exception
