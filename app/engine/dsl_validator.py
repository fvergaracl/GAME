"""
Structural validator for strategy ASTs.

Runs synchronously and without I/O. Called on every create/update so a
malformed AST never lands in the database, and called again by the
simulate service as a cheap idempotent guard — the second call is fast
because the AST has already been parsed by Pydantic into plain dict/list/
scalar values.

The validator enforces three things, in order:

1. **Shape**: every node has the required keys with the expected types
   (no surprise dict where a literal was expected, no missing ``when``
   on a rule).
2. **Whitelist**: ``compare.op``, ``arith.op``, ``field.path``, and
   ``node.type`` must all appear in the corresponding allow-list in
   ``dsl_ast``. The interpreter never invokes ``getattr`` on a node type
   string, but the validator is the first line of defence — by the time
   the AST reaches the handler table any unknown name has already been
   rejected with ``DslValidationError``.
3. **Limits**: a static node count and recursion depth are computed
   while walking. Both are bounded by ``configs.DSL_MAX_NODES`` and
   ``configs.DSL_MAX_DEPTH`` respectively, so an attacker can't smuggle
   in a billion-node tree that would otherwise OOM the API.

Auto-assigned IDs: nodes are allowed to omit ``id`` (Blockly will provide
them; hand-written JSON often skips them). The validator assigns a
deterministic ``"<parent_id>.<type>.<index>"`` slug so the interpreter
trace and any future error messages have a stable correlation key.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.config import configs
from app.core.exceptions import DslValidationError
from app.engine.dsl_ast import (
    ALLOWED_ARITH_OPS,
    ALLOWED_COMPARE_OPS,
    ALL_NODE_TYPES,
    CASE_NAME_MAX_LEN,
    CONDITION_NODE_TYPES,
    EXPRESSION_NODE_TYPES,
    NODE_AND,
    NODE_ARITH,
    NODE_ASSIGN_POINTS,
    NODE_COMPARE,
    NODE_FIELD,
    NODE_LITERAL,
    NODE_NOT,
    NODE_OR,
    NODE_PROGRAM,
    NODE_RETURN,
    NODE_RULE,
    NODE_SET_CALLBACK_DATA,
    RESERVED_PROGRAM_KEYS,
    STATEMENT_NODE_TYPES,
    is_known_field_path,
    is_valid_case_name,
)


_LITERAL_TYPES = (bool, int, float, str, type(None))
_CALLBACK_VALUE_LITERAL_TYPES = (bool, int, float, str, type(None))


def validate_ast(
    ast: Any,
    *,
    max_depth: Optional[int] = None,
    max_nodes: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Validate ``ast`` in place (mutates only to fill in missing ``id`` fields).

    Returns the same dict reference for convenience so callers can write
    ``ast = validate_ast(ast)``. Raises ``DslValidationError`` with a
    descriptive ``detail`` on any structural failure.

    The limits default to ``configs.DSL_*`` but tests can override them
    to exercise the rejection paths without sending a megabyte of JSON.
    """
    if max_depth is None:
        max_depth = configs.DSL_MAX_DEPTH
    if max_nodes is None:
        max_nodes = configs.DSL_MAX_NODES

    if not isinstance(ast, dict):
        raise DslValidationError(detail="AST root must be an object.")

    state = _State(max_depth=max_depth, max_nodes=max_nodes)
    _validate_program(ast, state=state)
    return ast


class _State:
    __slots__ = ("max_depth", "max_nodes", "node_count")

    def __init__(self, *, max_depth: int, max_nodes: int) -> None:
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.node_count = 0

    def step(self, node_id: str) -> None:
        self.node_count += 1
        if self.node_count > self.max_nodes:
            raise DslValidationError(
                detail=(
                    f"AST exceeds the maximum allowed node count "
                    f"({self.max_nodes})."
                ),
                headers={"X-Node-Id": node_id},
            )


def _require_type(node: Any, expected: str, *, parent_id: str) -> None:
    if not isinstance(node, dict):
        raise DslValidationError(
            detail=f"Expected node of type '{expected}', got {type(node).__name__}.",
            headers={"X-Node-Id": parent_id},
        )
    actual = node.get("type")
    if actual != expected:
        raise DslValidationError(
            detail=f"Expected node type '{expected}', got '{actual}'.",
            headers={"X-Node-Id": _node_id(node, parent_id, expected, 0)},
        )


def _node_id(node: Dict[str, Any], parent_id: str, type_hint: str, index: int) -> str:
    """Return the node's id, assigning a deterministic one if missing."""
    nid = node.get("id")
    if isinstance(nid, str) and nid:
        return nid
    new_id = f"{parent_id}.{type_hint}.{index}"
    node["id"] = new_id
    return new_id


def _assert_keys(
    node: Dict[str, Any], required: tuple, *, node_id: str, allowed_extra: tuple = ()
) -> None:
    for key in required:
        if key not in node:
            raise DslValidationError(
                detail=f"Node '{node.get('type')}' missing required key '{key}'.",
                headers={"X-Node-Id": node_id},
            )
    allowed = set(required) | set(allowed_extra) | {"type", "id"}
    extras = set(node.keys()) - allowed
    if extras:
        raise DslValidationError(
            detail=(
                f"Node '{node.get('type')}' has unexpected keys: "
                f"{sorted(extras)}."
            ),
            headers={"X-Node-Id": node_id},
        )


def _validate_program(node: Dict[str, Any], *, state: _State) -> None:
    nid = _node_id(node, "p", NODE_PROGRAM, 0)
    state.step(nid)
    _require_type(node, NODE_PROGRAM, parent_id="root")
    _assert_keys(
        node,
        ("rules",),
        node_id=nid,
        allowed_extra=("pre_rules", "post_rules", "default"),
    )

    rules = node.get("rules")
    if not isinstance(rules, list):
        raise DslValidationError(
            detail="program.rules must be an array.",
            headers={"X-Node-Id": nid},
        )
    for index, rule in enumerate(rules):
        _validate_rule(rule, parent_id=nid, index=index, state=state, depth=1)

    # Reserved sections — must be empty arrays until Sprint 7.
    for key in RESERVED_PROGRAM_KEYS:
        value = node.get(key)
        if value is None:
            continue
        if not isinstance(value, list) or len(value) > 0:
            raise DslValidationError(
                detail=(
                    f"program.{key} is reserved for future use; only empty "
                    "arrays are accepted in this version."
                ),
                headers={"X-Node-Id": nid},
            )

    default = node.get("default")
    if default is not None:
        _validate_statement(
            default, parent_id=nid, index=0, state=state, depth=1
        )


def _validate_rule(
    node: Any, *, parent_id: str, index: int, state: _State, depth: int
) -> None:
    if not isinstance(node, dict):
        raise DslValidationError(
            detail="program.rules[*] must be objects.",
            headers={"X-Node-Id": parent_id},
        )
    nid = _node_id(node, parent_id, NODE_RULE, index)
    state.step(nid)
    _require_type(node, NODE_RULE, parent_id=parent_id)
    _assert_keys(node, ("when", "then"), node_id=nid)
    _check_depth(depth, nid, state)

    when = node["when"]
    _validate_condition(when, parent_id=nid, index=0, state=state, depth=depth + 1)

    then = node["then"]
    if not isinstance(then, list) or not then:
        raise DslValidationError(
            detail="rule.then must be a non-empty array of statements.",
            headers={"X-Node-Id": nid},
        )
    for i, stmt in enumerate(then):
        _validate_statement(
            stmt, parent_id=nid, index=i, state=state, depth=depth + 1
        )


def _validate_condition(
    node: Any, *, parent_id: str, index: int, state: _State, depth: int
) -> None:
    if not isinstance(node, dict):
        raise DslValidationError(
            detail="Condition must be an object.",
            headers={"X-Node-Id": parent_id},
        )
    ntype = node.get("type")
    if ntype not in CONDITION_NODE_TYPES:
        raise DslValidationError(
            detail=f"Unknown condition node type: '{ntype}'.",
            headers={"X-Node-Id": parent_id},
        )
    nid = _node_id(node, parent_id, ntype, index)
    state.step(nid)
    _check_depth(depth, nid, state)

    if ntype == NODE_AND or ntype == NODE_OR:
        _assert_keys(node, ("args",), node_id=nid)
        args = node["args"]
        if not isinstance(args, list) or not args:
            raise DslValidationError(
                detail=f"{ntype}.args must be a non-empty array.",
                headers={"X-Node-Id": nid},
            )
        for i, arg in enumerate(args):
            _validate_condition(
                arg, parent_id=nid, index=i, state=state, depth=depth + 1
            )
        return

    if ntype == NODE_NOT:
        _assert_keys(node, ("arg",), node_id=nid)
        _validate_condition(
            node["arg"], parent_id=nid, index=0, state=state, depth=depth + 1
        )
        return

    if ntype == NODE_COMPARE:
        _assert_keys(node, ("op", "left", "right"), node_id=nid)
        op = node["op"]
        if op not in ALLOWED_COMPARE_OPS:
            raise DslValidationError(
                detail=f"compare.op '{op}' is not allowed.",
                headers={"X-Node-Id": nid},
            )
        _validate_expression(
            node["left"], parent_id=nid, index=0, state=state, depth=depth + 1
        )
        _validate_expression(
            node["right"], parent_id=nid, index=1, state=state, depth=depth + 1
        )
        return

    # Conditions can be raw booleans/expressions too (literal true/false,
    # or a field that resolves to a number used as truthy). Delegate.
    _validate_expression(
        node, parent_id=parent_id, index=index, state=state, depth=depth
    )


def _validate_expression(
    node: Any, *, parent_id: str, index: int, state: _State, depth: int
) -> None:
    if not isinstance(node, dict):
        raise DslValidationError(
            detail="Expression must be an object.",
            headers={"X-Node-Id": parent_id},
        )
    ntype = node.get("type")
    if ntype not in EXPRESSION_NODE_TYPES:
        raise DslValidationError(
            detail=f"Unknown expression node type: '{ntype}'.",
            headers={"X-Node-Id": parent_id},
        )
    nid = _node_id(node, parent_id, ntype, index)
    state.step(nid)
    _check_depth(depth, nid, state)

    if ntype == NODE_LITERAL:
        _assert_keys(node, ("value",), node_id=nid)
        value = node["value"]
        if not isinstance(value, _LITERAL_TYPES) or isinstance(value, bytes):
            raise DslValidationError(
                detail=(
                    "literal.value must be a JSON scalar (string, number, "
                    "boolean, or null)."
                ),
                headers={"X-Node-Id": nid},
            )
        return

    if ntype == NODE_FIELD:
        _assert_keys(node, ("path",), node_id=nid)
        path = node["path"]
        if not isinstance(path, str) or not path:
            raise DslValidationError(
                detail="field.path must be a non-empty string.",
                headers={"X-Node-Id": nid},
            )
        if not is_known_field_path(path):
            raise DslValidationError(
                detail=(
                    f"field.path '{path}' is not in the allowed set. "
                    "Either reference a whitelisted analytic path or use "
                    "'data.<key>' where <key> is [A-Za-z0-9_]+."
                ),
                headers={"X-Node-Id": nid},
            )
        return

    if ntype == NODE_ARITH:
        _assert_keys(node, ("op", "left", "right"), node_id=nid)
        op = node["op"]
        if op not in ALLOWED_ARITH_OPS:
            raise DslValidationError(
                detail=f"arith.op '{op}' is not allowed.",
                headers={"X-Node-Id": nid},
            )
        _validate_expression(
            node["left"], parent_id=nid, index=0, state=state, depth=depth + 1
        )
        _validate_expression(
            node["right"], parent_id=nid, index=1, state=state, depth=depth + 1
        )
        return


def _validate_statement(
    node: Any, *, parent_id: str, index: int, state: _State, depth: int
) -> None:
    if not isinstance(node, dict):
        raise DslValidationError(
            detail="Statement must be an object.",
            headers={"X-Node-Id": parent_id},
        )
    ntype = node.get("type")
    if ntype not in STATEMENT_NODE_TYPES:
        # If someone wrote an unknown node here, give a precise message.
        if ntype in ALL_NODE_TYPES:
            raise DslValidationError(
                detail=(
                    f"Node type '{ntype}' is not a valid statement "
                    "(expected assign_points, set_callback_data, or return)."
                ),
                headers={"X-Node-Id": parent_id},
            )
        raise DslValidationError(
            detail=f"Unknown statement node type: '{ntype}'.",
            headers={"X-Node-Id": parent_id},
        )
    nid = _node_id(node, parent_id, ntype, index)
    state.step(nid)
    _check_depth(depth, nid, state)

    if ntype == NODE_ASSIGN_POINTS:
        _assert_keys(node, ("value", "case_name"), node_id=nid)
        _validate_expression(
            node["value"], parent_id=nid, index=0, state=state, depth=depth + 1
        )
        case_name = node["case_name"]
        if not is_valid_case_name(case_name):
            raise DslValidationError(
                detail=(
                    "assign_points.case_name must be 1-"
                    f"{CASE_NAME_MAX_LEN} printable ASCII characters."
                ),
                headers={"X-Node-Id": nid},
            )
        return

    if ntype == NODE_SET_CALLBACK_DATA:
        _assert_keys(node, ("key", "value"), node_id=nid)
        key = node["key"]
        if not isinstance(key, str) or not key:
            raise DslValidationError(
                detail="set_callback_data.key must be a non-empty string.",
                headers={"X-Node-Id": nid},
            )
        # value may be a full expression — the interpreter will resolve it.
        _validate_expression(
            node["value"], parent_id=nid, index=0, state=state, depth=depth + 1
        )
        return

    if ntype == NODE_RETURN:
        _assert_keys(node, (), node_id=nid)
        return


def _check_depth(depth: int, node_id: str, state: _State) -> None:
    if depth > state.max_depth:
        raise DslValidationError(
            detail=(
                f"AST nesting depth exceeds the maximum allowed "
                f"({state.max_depth})."
            ),
            headers={"X-Node-Id": node_id},
        )
