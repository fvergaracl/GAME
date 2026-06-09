"""
Interpreter walker tests.

Each test builds a small AST, runs it through the validator (so the
inputs match what the simulate endpoint would accept), then through the
interpreter. The asserts pin: early-return semantics, callback
accumulation, arithmetic/comparison correctness, and the runtime guards
that enforce the node-count, depth, and timeout limits.
"""

import asyncio
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import DslExecutionError, DslLimitExceededError
from app.engine.dsl_execution_context import ExecutionContext
from app.engine.dsl_interpreter import DslInterpreter
from app.engine.dsl_validator import validate_ast


def _two_branch_program():
    return {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {
                    "type": "compare",
                    "id": "c1",
                    "op": "<",
                    "left": {
                        "type": "field",
                        "id": "f1",
                        "path": "user.measurements_count",
                    },
                    "right": {"type": "literal", "id": "l1", "value": 2},
                },
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a1",
                        "value": {"type": "literal", "id": "lv1", "value": 1},
                        "case_name": "BasicEngagement",
                    }
                ],
            },
            {
                "type": "rule",
                "id": "r2",
                "when": {"type": "literal", "id": "l2", "value": True},
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a2",
                        "value": {"type": "literal", "id": "lv2", "value": 10},
                        "case_name": "PerformanceBonus",
                    }
                ],
            },
        ],
    }


async def _build_ctx(ast, **overrides):
    return await ExecutionContext.build_for_ast(
        ast,
        externalGameId=overrides.get("externalGameId", "g"),
        externalTaskId=overrides.get("externalTaskId", "t"),
        externalUserId=overrides.get("externalUserId", "u"),
        data=overrides.get("data"),
        analytics_service=MagicMock(),
        mock_state=overrides.get("mock_state", {}),
    )


def _interpreter(**overrides):
    return DslInterpreter(
        max_nodes=overrides.get("max_nodes", 1000),
        max_depth=overrides.get("max_depth", 32),
        yield_every=overrides.get("yield_every", 64),
    )


@pytest.mark.asyncio
async def test_first_rule_matches_returns_basic_engagement():
    ast = _two_branch_program()
    validate_ast(ast)
    ctx = await _build_ctx(ast, mock_state={"user.measurements_count": 1})

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 1
    assert result["case_name"] == "BasicEngagement"
    assert any(
        e["nodeId"] == "a1" and e["type"] == "assign_points" for e in result["trace"]
    )


@pytest.mark.asyncio
async def test_falls_through_to_second_rule():
    ast = _two_branch_program()
    validate_ast(ast)
    ctx = await _build_ctx(ast, mock_state={"user.measurements_count": 5})

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 10
    assert result["case_name"] == "PerformanceBonus"


@pytest.mark.asyncio
async def test_first_assign_points_short_circuits_within_then():
    """Multiple assign_points in one rule: only the first one wins."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {"type": "literal", "id": "lt", "value": True},
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a1",
                        "value": {"type": "literal", "id": "lv1", "value": 7},
                        "case_name": "first",
                    },
                    {
                        "type": "assign_points",
                        "id": "a2",
                        "value": {"type": "literal", "id": "lv2", "value": 99},
                        "case_name": "second",
                    },
                ],
            }
        ],
    }
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 7
    assert result["case_name"] == "first"
    assert not any(e["nodeId"] == "a2" for e in result["trace"])


@pytest.mark.asyncio
async def test_callback_data_accumulates_before_assign_points():
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {"type": "literal", "id": "lt", "value": True},
                "then": [
                    {
                        "type": "set_callback_data",
                        "id": "s1",
                        "key": "bonus_kind",
                        "value": {"type": "literal", "id": "lk", "value": "perf"},
                    },
                    {
                        "type": "set_callback_data",
                        "id": "s2",
                        "key": "level",
                        "value": {"type": "literal", "id": "lv", "value": 3},
                    },
                    {
                        "type": "assign_points",
                        "id": "a1",
                        "value": {"type": "literal", "id": "lvv", "value": 4},
                        "case_name": "done",
                    },
                ],
            }
        ],
    }
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 4
    assert result["callback_data"] == {"bonus_kind": "perf", "level": 3}


@pytest.mark.asyncio
async def test_default_block_runs_when_no_rule_matches():
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {"type": "literal", "id": "lf", "value": False},
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a1",
                        "value": {"type": "literal", "id": "lv", "value": 1},
                        "case_name": "skipped",
                    }
                ],
            }
        ],
        "default": {
            "type": "assign_points",
            "id": "d1",
            "value": {"type": "literal", "id": "dv", "value": 0},
            "case_name": "default",
        },
    }
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 0
    assert result["case_name"] == "default"


@pytest.mark.asyncio
async def test_no_rule_no_default_returns_zero():
    ast = {"type": "program", "id": "p", "rules": []}
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 0
    assert result["case_name"] is None
    assert result["callback_data"] == {}


@pytest.mark.asyncio
async def test_arith_addition_and_field_resolution():
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {"type": "literal", "id": "lt", "value": True},
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a1",
                        "value": {
                            "type": "arith",
                            "id": "ar",
                            "op": "+",
                            "left": {
                                "type": "field",
                                "id": "f1",
                                "path": "user.measurements_count",
                            },
                            "right": {"type": "literal", "id": "ll", "value": 10},
                        },
                        "case_name": "computed",
                    }
                ],
            }
        ],
    }
    validate_ast(ast)
    ctx = await _build_ctx(ast, mock_state={"user.measurements_count": 5})

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 15


# ---------------------------------------------------------------------------
# Sprint 6: positive coverage for the new arith ops (min/max) and the
# func_call node (int, clamp). The adversarial suite covers the rejection
# paths; these tests pin the happy-path numeric outputs.
# ---------------------------------------------------------------------------


def _wrap_value_into_assign_program(value_expr):
    """Single-rule program whose only ``then`` is ``assign_points value``."""
    return {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r",
                "when": {"type": "literal", "id": "lt", "value": True},
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a",
                        "value": value_expr,
                        "case_name": "computed",
                    }
                ],
            }
        ],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "op,left,right,expected",
    [
        ("min", 3, 5, 3),
        ("min", 5, 3, 3),
        ("max", 3, 5, 5),
        ("max", 5, 3, 5),
        ("min", 2.5, 2.5, 2.5),  # equal values resolve to either; min picks left
    ],
)
async def test_arith_min_max(op, left, right, expected):
    ast = _wrap_value_into_assign_program(
        {
            "type": "arith",
            "id": "ar",
            "op": op,
            "left": {"type": "literal", "id": "ll", "value": left},
            "right": {"type": "literal", "id": "lr", "value": right},
        }
    )
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == expected


@pytest.mark.asyncio
async def test_func_call_int_truncates_toward_zero():
    """int() in Python truncates (not rounds). Mirrors ``int(2.7) == 2``
    semantics in constantEffortStrategy.py:53."""
    ast = _wrap_value_into_assign_program(
        {
            "type": "func_call",
            "id": "fc",
            "name": "int",
            "args": [{"type": "literal", "id": "l", "value": 2.7}],
        }
    )
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "value,lo,hi,expected",
    [
        (50, 1, 100, 50),  # value within range
        (-5, 1, 100, 1),  # below floor
        (150, 1, 100, 100),  # above ceiling
        (1, 1, 100, 1),  # at floor (inclusive)
        (100, 1, 100, 100),  # at ceiling (inclusive)
    ],
)
async def test_func_call_clamp(value, lo, hi, expected):
    ast = _wrap_value_into_assign_program(
        {
            "type": "func_call",
            "id": "fc",
            "name": "clamp",
            "args": [
                {"type": "literal", "id": "lv", "value": value},
                {"type": "literal", "id": "llo", "value": lo},
                {"type": "literal", "id": "lhi", "value": hi},
            ],
        }
    )
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == expected


@pytest.mark.asyncio
async def test_division_by_zero_raises_execution_error():
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {"type": "literal", "id": "lt", "value": True},
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a1",
                        "value": {
                            "type": "arith",
                            "id": "ar",
                            "op": "/",
                            "left": {"type": "literal", "id": "ll", "value": 10},
                            "right": {"type": "literal", "id": "lr", "value": 0},
                        },
                        "case_name": "doomed",
                    }
                ],
            }
        ],
    }
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    with pytest.raises(DslExecutionError, match="division by zero"):
        await _interpreter().execute(ast, ctx)


@pytest.mark.asyncio
async def test_compare_type_mismatch_raises_execution_error():
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {
                    "type": "compare",
                    "id": "c",
                    "op": "<",
                    "left": {"type": "literal", "id": "ll", "value": "text"},
                    "right": {"type": "literal", "id": "lr", "value": 1},
                },
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a1",
                        "value": {"type": "literal", "id": "lv", "value": 1},
                        "case_name": "x",
                    }
                ],
            }
        ],
    }
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    with pytest.raises(DslExecutionError, match="incompatible types"):
        await _interpreter().execute(ast, ctx)


@pytest.mark.asyncio
async def test_runtime_node_count_limit_triggers():
    """Build an AST the validator accepts but cap the interpreter limit."""
    ast = _two_branch_program()
    validate_ast(ast)
    ctx = await _build_ctx(ast, mock_state={"user.measurements_count": 1})

    with pytest.raises(DslLimitExceededError, match="node count"):
        await _interpreter(max_nodes=3).execute(ast, ctx)


@pytest.mark.asyncio
async def test_runtime_depth_limit_triggers():
    # Three nested AND wrappers around a simple compare → depth ≥ 4.
    leaf = {
        "type": "compare",
        "id": "c",
        "op": "==",
        "left": {"type": "literal", "id": "ll", "value": 1},
        "right": {"type": "literal", "id": "lr", "value": 1},
    }
    nested = leaf
    for i in range(3):
        nested = {"type": "and", "id": f"a{i}", "args": [nested]}
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": nested,
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a1",
                        "value": {"type": "literal", "id": "lv", "value": 1},
                        "case_name": "x",
                    }
                ],
            }
        ],
    }
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    with pytest.raises(DslLimitExceededError, match="depth"):
        await _interpreter(max_depth=3).execute(ast, ctx)


@pytest.mark.asyncio
async def test_timeout_cancels_interpreter():
    """
    Forces a wait_for cancellation by stubbing the interpreter step to
    sleep longer than the timeout. Confirms the cooperative-yield
    pattern actually lets asyncio cancel mid-walk.
    """
    ast = _two_branch_program()
    validate_ast(ast)
    ctx = await _build_ctx(ast, mock_state={"user.measurements_count": 1})

    interpreter = _interpreter(yield_every=1)

    async def _slow_yield(state):  # type: ignore[no-untyped-def]
        await asyncio.sleep(0.2)

    interpreter._maybe_yield = _slow_yield  # type: ignore[assignment]

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(interpreter.execute(ast, ctx), timeout=0.05)


# --- else / else-if branches ------------------------------------------------


def _assign(node_id, value, case_name):
    return {
        "type": "assign_points",
        "id": node_id,
        "value": {"type": "literal", "id": f"{node_id}_v", "value": value},
        "case_name": case_name,
    }


def _branching_rule_program(when_value):
    """One rule: when→THEN, two else_ifs, and an else. Conditions are bare
    literals so the chosen branch is fully controlled by the test."""
    return {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {"type": "literal", "id": "w", "value": when_value},
                "then": [_assign("a_then", 1, "THEN")],
                "else_if": [
                    {
                        "when": {"type": "literal", "id": "e0", "value": False},
                        "then": [_assign("a_e0", 2, "ELIF0")],
                    },
                    {
                        "when": {"type": "literal", "id": "e1", "value": True},
                        "then": [_assign("a_e1", 3, "ELIF1")],
                    },
                ],
                "else": [_assign("a_else", 4, "ELSE")],
            }
        ],
    }


@pytest.mark.asyncio
async def test_then_branch_runs_when_condition_true():
    ast = _branching_rule_program(when_value=True)
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 1
    assert result["case_name"] == "THEN"
    assert any(e["type"] == "rule" and e["branch"] == "match" for e in result["trace"])
    # No else / else_if statement ran.
    assert not any(e["nodeId"] == "a_e1" for e in result["trace"])


@pytest.mark.asyncio
async def test_first_matching_else_if_wins():
    # when=False → else_if[0] (False) skipped → else_if[1] (True) runs.
    ast = _branching_rule_program(when_value=False)
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 3
    assert result["case_name"] == "ELIF1"
    assert any(
        e["type"] == "rule" and e["branch"] == "elseif:1" for e in result["trace"]
    )
    # The else branch must NOT run once an else_if matched.
    assert not any(e["nodeId"] == "a_else" for e in result["trace"])


@pytest.mark.asyncio
async def test_else_runs_when_nothing_matches():
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {"type": "literal", "id": "w", "value": False},
                "then": [_assign("a_then", 1, "THEN")],
                "else_if": [
                    {
                        "when": {"type": "literal", "id": "e0", "value": False},
                        "then": [_assign("a_e0", 2, "ELIF0")],
                    },
                ],
                "else": [_assign("a_else", 4, "ELSE")],
            }
        ],
    }
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 4
    assert result["case_name"] == "ELSE"
    assert any(e["type"] == "rule" and e["branch"] == "else" for e in result["trace"])


@pytest.mark.asyncio
async def test_no_match_without_else_is_noop():
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {"type": "literal", "id": "w", "value": False},
                "then": [_assign("a_then", 1, "THEN")],
                "else_if": [
                    {
                        "when": {"type": "literal", "id": "e0", "value": False},
                        "then": [_assign("a_e0", 2, "ELIF0")],
                    },
                ],
            }
        ],
    }
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 0
    assert result["case_name"] is None
    assert any(e["type"] == "rule" and e["branch"] == "skip" for e in result["trace"])


@pytest.mark.asyncio
async def test_else_branch_falls_through_to_next_rule_when_non_halting():
    """An else branch that only sets callback data (no assign_points) must
    not halt - execution falls through to the next rule, exactly like a
    non-halting then branch does."""
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {"type": "literal", "id": "w", "value": False},
                "then": [_assign("a_then", 1, "THEN")],
                "else": [
                    {
                        "type": "set_callback_data",
                        "id": "cb",
                        "key": "note",
                        "value": {"type": "literal", "id": "cbv", "value": "x"},
                    }
                ],
            },
            {
                "type": "rule",
                "id": "r2",
                "when": {"type": "literal", "id": "w2", "value": True},
                "then": [_assign("a2", 9, "SECOND")],
            },
        ],
    }
    validate_ast(ast)
    ctx = await _build_ctx(ast)

    result = await _interpreter().execute(ast, ctx)

    assert result["points"] == 9
    assert result["case_name"] == "SECOND"
    assert result["callback_data"]["note"] == "x"
