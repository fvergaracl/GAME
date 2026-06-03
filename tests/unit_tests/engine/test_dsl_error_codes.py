"""
Sprint 10: DSL errors carry stable codes for the frontend i18n layer.

The interpreter, validator and simulation service all emit
``DslValidationError`` / ``DslExecutionError`` / ``DslLimitExceededError``
/ ``DslTimeoutError`` with a ``code`` kwarg whose value is a stable
``DSL_*`` constant. The frontend's ``errorCodes.js`` consumes these
codes; this test ensures the backend keeps producing the expected
identifiers so the contract doesn't drift silently.

The detail body for a coded error is a dict (``{code, params, message}``)
so the FastAPI HTTPException response keeps the structure. Legacy raises
that haven't been migrated still emit a bare string detail — the helper
``_assert_code`` asserts the structured shape only when ``code`` is set.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import (DslExecutionError, DslLimitExceededError,
                                 DslTimeoutError, DslValidationError)
from app.engine.dsl_execution_context import ExecutionContext
from app.engine.dsl_interpreter import DslInterpreter
from app.engine.dsl_validator import validate_ast


def _assert_code(exc, expected_code, **expected_params):
    """Pin both the class metadata and the serialised detail body."""
    assert exc.code == expected_code
    assert isinstance(
        exc.detail, dict
    ), f"DSL errors with a code must have a dict detail; got {type(exc.detail)}"
    assert exc.detail.get("code") == expected_code
    assert isinstance(exc.detail.get("params"), dict)
    for key, value in expected_params.items():
        assert exc.detail["params"].get(key) == value, (
            f"expected params.{key}={value!r}, got "
            f"{exc.detail['params'].get(key)!r}"
        )
    # ``message`` is the English fallback for logs/tests/legacy callers.
    assert exc.detail.get("message"), "structured detail must carry a fallback message"


def test_legacy_string_detail_still_works():
    """No regression: raises without ``code`` keep their pre-Sprint-10 shape."""
    exc = DslValidationError(detail="legacy message")
    assert exc.code is None
    assert exc.detail == "legacy message"


def test_division_by_zero_emits_code():
    exc = DslExecutionError(
        detail="division by zero",
        code="DSL_ARITH_DIV_BY_ZERO",
        params={"nodeId": "abc", "op": "/"},
    )
    _assert_code(exc, "DSL_ARITH_DIV_BY_ZERO", nodeId="abc", op="/")


def test_validation_field_path_not_allowed():
    bad_ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r",
                "when": {
                    "type": "compare",
                    "id": "c",
                    "op": "<",
                    "left": {
                        "type": "field",
                        "id": "f",
                        "path": "user.evil_secret",
                    },
                    "right": {"type": "literal", "id": "l", "value": 1},
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
    with pytest.raises(DslValidationError) as info:
        validate_ast(bad_ast)
    _assert_code(info.value, "DSL_FIELD_PATH_NOT_ALLOWED", path="user.evil_secret")


def test_validation_arith_op_not_allowed():
    bad_ast = {
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
                        "value": {
                            "type": "arith",
                            "id": "ar",
                            "op": "%",  # not in ALLOWED_ARITH_OPS
                            "left": {
                                "type": "literal",
                                "id": "ll",
                                "value": 1,
                            },
                            "right": {
                                "type": "literal",
                                "id": "lr",
                                "value": 2,
                            },
                        },
                        "case_name": "x",
                    }
                ],
            }
        ],
    }
    with pytest.raises(DslValidationError) as info:
        validate_ast(bad_ast)
    _assert_code(info.value, "DSL_ARITH_OP_NOT_ALLOWED", op="%")


def test_validation_func_name_not_allowed():
    bad_ast = {
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
                        "value": {
                            "type": "func_call",
                            "id": "fc",
                            "name": "eval",  # not in ALLOWED_FUNC_NAMES
                            "args": [
                                {"type": "literal", "id": "lt2", "value": 1},
                            ],
                        },
                        "case_name": "x",
                    }
                ],
            }
        ],
    }
    with pytest.raises(DslValidationError) as info:
        validate_ast(bad_ast)
    _assert_code(info.value, "DSL_FUNC_NAME_NOT_ALLOWED", name="eval")


@pytest.mark.asyncio
async def test_runtime_division_by_zero_emits_code():
    ast = {
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
                        "value": {
                            "type": "arith",
                            "id": "ar",
                            "op": "/",
                            "left": {"type": "literal", "id": "l1", "value": 1},
                            "right": {"type": "literal", "id": "l2", "value": 0},
                        },
                        "case_name": "x",
                    }
                ],
            }
        ],
    }
    validate_ast(ast)
    ctx = await ExecutionContext.build_for_ast(
        ast,
        externalGameId="g",
        externalTaskId="t",
        externalUserId="u",
        data=None,
        analytics_service=MagicMock(),
        mock_state={},
    )

    interpreter = DslInterpreter(max_nodes=200, max_depth=32)
    with pytest.raises(DslExecutionError) as info:
        await interpreter.execute(ast, ctx)
    _assert_code(info.value, "DSL_ARITH_DIV_BY_ZERO", op="/")


def test_limit_exceeded_keeps_412_status():
    """The PreconditionFailed base class still sets HTTP 412."""
    exc = DslLimitExceededError(
        detail="too deep",
        code="DSL_LIMIT_DEPTH",
        params={"max": 32},
    )
    assert exc.status_code == 412
    _assert_code(exc, "DSL_LIMIT_DEPTH", max=32)


def test_timeout_keeps_412_status():
    exc = DslTimeoutError(
        detail="too slow",
        code="DSL_TIMEOUT",
        params={"timeoutMs": 500},
    )
    assert exc.status_code == 412
    _assert_code(exc, "DSL_TIMEOUT", timeoutMs=500)


def test_asyncio_loop_runs():
    """Sanity guard: pytest-asyncio is wired and we can still run a loop here."""
    assert asyncio.get_event_loop_policy() is not None
