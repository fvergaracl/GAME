"""
Structural validator tests.

Covers happy paths, missing keys, unknown node types, unknown field
paths, and the node-count / depth guards. Adversarial inputs that try
to escape the sandbox live in ``test_dsl_adversarial.py`` so the two
suites can be reasoned about independently.
"""

import pytest

from app.core.exceptions import DslValidationError
from app.engine.dsl_validator import validate_ast


def _basic_rule():
    return {
        "type": "rule",
        "id": "r1",
        "when": {
            "type": "compare",
            "id": "c1",
            "op": "<",
            "left": {"type": "field", "id": "f1", "path": "user.measurements_count"},
            "right": {"type": "literal", "id": "l1", "value": 2},
        },
        "then": [
            {
                "type": "assign_points",
                "id": "a1",
                "value": {"type": "literal", "id": "l2", "value": 1},
                "case_name": "BasicEngagement",
            }
        ],
    }


def test_validator_accepts_minimal_program():
    ast = {"type": "program", "id": "p", "rules": [_basic_rule()]}
    assert validate_ast(ast) is ast


def test_validator_accepts_program_with_default_and_reserved_sections():
    ast = {
        "type": "program",
        "id": "p",
        "pre_rules": [],
        "post_rules": [],
        "rules": [_basic_rule()],
        "default": {
            "type": "assign_points",
            "id": "d",
            "value": {"type": "literal", "id": "dl", "value": 0},
            "case_name": "default",
        },
    }
    validate_ast(ast)


def test_validator_rejects_non_object_root():
    with pytest.raises(DslValidationError, match="object"):
        validate_ast([])


def test_validator_rejects_wrong_root_type():
    with pytest.raises(DslValidationError):
        validate_ast({"type": "rule", "rules": []})


def test_validator_rejects_unknown_node_type_inside_condition():
    rule = _basic_rule()
    rule["when"] = {"type": "eval", "id": "c1", "code": "1+1"}
    ast = {"type": "program", "id": "p", "rules": [rule]}
    with pytest.raises(DslValidationError, match="Unknown condition"):
        validate_ast(ast)


def test_validator_rejects_unknown_field_path():
    rule = _basic_rule()
    rule["when"]["left"]["path"] = "user.password"
    ast = {"type": "program", "id": "p", "rules": [rule]}
    with pytest.raises(DslValidationError, match="not in the allowed set"):
        validate_ast(ast)


def test_validator_accepts_data_dot_arbitrary_key():
    rule = _basic_rule()
    rule["when"]["left"]["path"] = "data.payload_bonus"
    ast = {"type": "program", "id": "p", "rules": [rule]}
    validate_ast(ast)


def test_validator_rejects_bad_data_path_with_dots():
    rule = _basic_rule()
    rule["when"]["left"]["path"] = "data.nested.field"
    ast = {"type": "program", "id": "p", "rules": [rule]}
    with pytest.raises(DslValidationError):
        validate_ast(ast)


def test_validator_rejects_bad_compare_op():
    rule = _basic_rule()
    rule["when"]["op"] = "==="
    ast = {"type": "program", "id": "p", "rules": [rule]}
    with pytest.raises(DslValidationError, match="compare.op"):
        validate_ast(ast)


def test_validator_rejects_bad_arith_op():
    rule = _basic_rule()
    rule["when"]["right"] = {
        "type": "arith",
        "id": "ar1",
        "op": "**",
        "left": {"type": "literal", "id": "ll", "value": 2},
        "right": {"type": "literal", "id": "rr", "value": 3},
    }
    ast = {"type": "program", "id": "p", "rules": [rule]}
    with pytest.raises(DslValidationError, match="arith.op"):
        validate_ast(ast)


def test_validator_rejects_missing_required_keys_on_rule():
    rule = {"type": "rule", "id": "r1", "then": []}
    ast = {"type": "program", "id": "p", "rules": [rule]}
    with pytest.raises(DslValidationError, match="missing required key"):
        validate_ast(ast)


def test_validator_rejects_empty_then():
    rule = _basic_rule()
    rule["then"] = []
    ast = {"type": "program", "id": "p", "rules": [rule]}
    with pytest.raises(DslValidationError, match="non-empty array"):
        validate_ast(ast)


def test_validator_rejects_bad_case_name():
    rule = _basic_rule()
    rule["then"][0]["case_name"] = "abc\x00def"
    ast = {"type": "program", "id": "p", "rules": [rule]}
    with pytest.raises(DslValidationError, match="case_name"):
        validate_ast(ast)


def test_validator_rejects_oversized_case_name():
    rule = _basic_rule()
    rule["then"][0]["case_name"] = "x" * 201
    ast = {"type": "program", "id": "p", "rules": [rule]}
    with pytest.raises(DslValidationError):
        validate_ast(ast)


def test_validator_rejects_node_count_overflow():
    rules = [_basic_rule() for _ in range(50)]
    ast = {"type": "program", "id": "p", "rules": rules}
    with pytest.raises(DslValidationError, match="node count"):
        validate_ast(ast, max_nodes=20)


def test_validator_rejects_depth_overflow():
    inner = {"type": "literal", "id": "l", "value": True}
    for i in range(40):
        inner = {"type": "not", "id": f"n{i}", "arg": inner}
    rule = _basic_rule()
    rule["when"] = inner
    ast = {"type": "program", "id": "p", "rules": [rule]}
    with pytest.raises(DslValidationError, match="depth"):
        validate_ast(ast, max_depth=5)


def test_validator_assigns_ids_when_missing():
    rule = {
        "type": "rule",
        "when": {"type": "literal", "value": True},
        "then": [
            {
                "type": "assign_points",
                "value": {"type": "literal", "value": 1},
                "case_name": "x",
            }
        ],
    }
    ast = {"type": "program", "rules": [rule]}
    validate_ast(ast)
    assert ast["id"]
    assert rule["id"]
    assert rule["when"]["id"]
    assert rule["then"][0]["id"]
    # Re-validating must be idempotent (ids stay stable).
    snapshot = ast["id"], rule["id"], rule["then"][0]["id"]
    validate_ast(ast)
    assert (ast["id"], rule["id"], rule["then"][0]["id"]) == snapshot


def test_validator_rejects_assign_points_inside_pre_rules():
    # Sprint 7: pre_rules are no longer reserved-empty. They CAN be
    # non-empty, but only statements valid in the 'pre' context
    # (set_data, veto, set_callback_data, return) are accepted.
    # ``_basic_rule`` builds an assign_points inside, which belongs to
    # main rules and must be rejected when placed in pre_rules.
    ast = {
        "type": "program",
        "id": "p",
        "rules": [_basic_rule()],
        "pre_rules": [_basic_rule()],
    }
    with pytest.raises(
        DslValidationError,
        match="'assign_points' is not allowed inside 'pre'",
    ):
        validate_ast(ast)


def test_validator_accepts_pre_rules_with_set_data_statement():
    # Sprint 7: a pre-rule with a context-appropriate statement
    # (set_data) is valid. This is the happy path that lets DSL_EXTEND
    # mutate ``data`` before the parent built-in runs.
    pre_rule = {
        "type": "rule",
        "id": "pr1",
        "when": {"type": "literal", "id": "lt", "value": True},
        "then": [
            {
                "type": "set_data",
                "id": "sd1",
                "key": "is_first_time",
                "value": {"type": "literal", "id": "lv", "value": True},
            }
        ],
    }
    ast = {
        "type": "program",
        "id": "p",
        "rules": [_basic_rule()],
        "pre_rules": [pre_rule],
    }
    validate_ast(ast)


def test_validator_rejects_unexpected_keys_on_node():
    rule = _basic_rule()
    rule["sneaky"] = "value"
    ast = {"type": "program", "id": "p", "rules": [rule]}
    with pytest.raises(DslValidationError, match="unexpected keys"):
        validate_ast(ast)
