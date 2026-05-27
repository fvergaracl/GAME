"""
Sandbox-escape adversarial tests.

Every payload in this file is something a malicious tenant might try to
ship through ``POST /v1/strategies/custom``. Each is expected to be
rejected by ``validate_ast`` BEFORE the interpreter ever sees it; if any
of these started to "execute" silently we would have lost the sandbox
guarantees and the whole DSL roadmap would have to be paused.

Failures here are critical — do not weaken assertions to make a test
pass without first re-evaluating the threat model.
"""

from unittest.mock import MagicMock

import pytest

from app.core.exceptions import DslValidationError
from app.engine.dsl_execution_context import ExecutionContext
from app.engine.dsl_interpreter import DslInterpreter
from app.engine.dsl_validator import validate_ast


_VALID_PROGRAM_TEMPLATE = {
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
                    "value": {"type": "literal", "id": "lv", "value": 1},
                    "case_name": "ok",
                }
            ],
        }
    ],
}


def _wrap_field_path(path):
    """Build a minimal program with the given field path embedded."""
    return {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r",
                "when": {
                    "type": "compare",
                    "id": "c",
                    "op": "==",
                    "left": {"type": "field", "id": "f", "path": path},
                    "right": {"type": "literal", "id": "lr", "value": 0},
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


@pytest.mark.parametrize(
    "path",
    [
        "__builtins__",
        "__import__",
        "__class__",
        "__mro__",
        "os.system",
        "subprocess.Popen",
        "self.user_points_analytics_service",
        "user.password",
        "user.__init__",
        "data..oops",
        "data.with.dots",
        "data. ",
        "",
    ],
)
def test_validator_rejects_dangerous_field_paths(path):
    with pytest.raises(DslValidationError):
        validate_ast(_wrap_field_path(path))


@pytest.mark.parametrize(
    "node_type",
    [
        "eval",
        "exec",
        "import",
        "function_call",
        "lambda",
        "getattr",
        "raise",
    ],
)
def test_validator_rejects_unknown_top_level_node_types(node_type):
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r",
                "when": {"type": node_type, "id": "c"},
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
    with pytest.raises(DslValidationError):
        validate_ast(ast)


def test_validator_rejects_compare_op_with_attribute_access_attempt():
    rule_ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r",
                "when": {
                    "type": "compare",
                    "id": "c",
                    "op": "__class__",
                    "left": {"type": "literal", "id": "ll", "value": 1},
                    "right": {"type": "literal", "id": "lr", "value": 1},
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
    with pytest.raises(DslValidationError):
        validate_ast(rule_ast)


def test_validator_rejects_arith_op_with_dunder():
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
                            "op": "__pow__",
                            "left": {"type": "literal", "id": "ll", "value": 2},
                            "right": {"type": "literal", "id": "lr", "value": 3},
                        },
                        "case_name": "x",
                    }
                ],
            }
        ],
    }
    with pytest.raises(DslValidationError):
        validate_ast(ast)


def test_validator_rejects_literal_holding_a_dict():
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
                    "op": "==",
                    "left": {
                        "type": "literal",
                        "id": "l",
                        "value": {"__class__": "object"},
                    },
                    "right": {"type": "literal", "id": "lr", "value": 1},
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
    with pytest.raises(DslValidationError, match="literal.value"):
        validate_ast(ast)


def test_validator_rejects_case_name_with_control_bytes():
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
                        "value": {"type": "literal", "id": "lv", "value": 1},
                        "case_name": "ev\x00il",
                    }
                ],
            }
        ],
    }
    with pytest.raises(DslValidationError, match="case_name"):
        validate_ast(bad_ast)


def test_validator_rejects_massive_node_count_via_recursive_and():
    arg = {"type": "literal", "id": "lt", "value": True}
    args = [arg for _ in range(2000)]
    ast = {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r",
                "when": {"type": "and", "id": "an", "args": args},
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
    with pytest.raises(DslValidationError, match="node count"):
        validate_ast(ast)


def test_validator_rejects_extra_program_keys():
    bad = dict(_VALID_PROGRAM_TEMPLATE)
    bad["pre_rules"] = []
    bad["evil_payload"] = "ignore_me"
    with pytest.raises(DslValidationError, match="unexpected keys"):
        validate_ast(bad)


@pytest.mark.asyncio
async def test_runtime_rejects_unknown_node_if_validator_bypassed():
    """
    Defence in depth: if a corrupt AST somehow reaches the interpreter
    without going through the validator, dispatch must still refuse to
    invoke any handler that isn't in the whitelist.
    """
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
                        "type": "sneaky_eval",
                        "id": "s",
                        "code": "1+1",
                    }
                ],
            }
        ],
    }
    ctx = await ExecutionContext.build_for_ast(
        ast,
        externalGameId="g",
        externalTaskId="t",
        externalUserId="u",
        data=None,
        analytics_service=MagicMock(),
    )
    interpreter = DslInterpreter(max_nodes=100, max_depth=10)
    with pytest.raises(DslValidationError, match="Unknown statement"):
        await interpreter.execute(ast, ctx)
