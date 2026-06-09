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
from app.engine.dsl_ast import (ALL_NODE_TYPES, ALLOWED_ARITH_OPS, ALLOWED_COMPARE_OPS,
                                ALLOWED_FUNC_NAMES, CASE_NAME_MAX_LEN,
                                CONDITION_NODE_TYPES, EXPRESSION_NODE_TYPES, FUNC_ARITY,
                                NODE_AND, NODE_ARITH, NODE_ASSIGN_POINTS, NODE_COMPARE,
                                NODE_FIELD, NODE_FUNC_CALL, NODE_LITERAL, NODE_NOT,
                                NODE_OR, NODE_PROGRAM, NODE_RETURN, NODE_RULE,
                                NODE_SET_CALLBACK_DATA, NODE_SET_CASE_NAME,
                                NODE_SET_DATA, NODE_SET_POINTS, NODE_VETO,
                                PARENT_VARIABLES_KEY, STATEMENT_ALLOWED_CONTEXTS,
                                STATEMENT_NODE_TYPES, is_known_field_path,
                                is_parent_field_path, is_valid_case_name,
                                is_valid_data_path)

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
        """
        Count one visited node and enforce the AST node-count budget.

        Args:
            node_id (str): Id of the node being visited (reported on error).

        Raises:
            DslValidationError: If the running node count exceeds
                ``max_nodes``.
        """
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
    """
    Assert that ``node`` is a dict whose ``type`` equals ``expected``.

    Args:
        node (Any): Candidate AST node.
        expected (str): The required node ``type``.
        parent_id (str): Id of the enclosing node, used in error reporting.

    Raises:
        DslValidationError: If ``node`` is not a dict or has the wrong type.
    """
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
    """
    Validate that a node has all required keys and no unexpected ones.

    ``type`` and ``id`` are always permitted in addition to ``required`` and
    ``allowed_extra``.

    Args:
        node (Dict[str, Any]): The AST node to check.
        required (tuple): Keys that must be present.
        node_id (str): Id of the node, used in error reporting.
        allowed_extra (tuple): Additional optional keys to permit.

    Raises:
        DslValidationError: If a required key is missing or an unknown key is
            present.
    """
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
                f"Node '{node.get('type')}' has unexpected keys: " f"{sorted(extras)}."
            ),
            headers={"X-Node-Id": node_id},
        )


def _validate_program(node: Dict[str, Any], *, state: _State) -> None:
    """
    Validate the top-level ``program`` node and recurse into its rules.

    Args:
        node (Dict[str, Any]): The program AST node.
        state (_State): Shared validation state tracking node/depth budgets.

    Raises:
        DslValidationError: If the program node or any descendant is invalid.
    """
    nid = _node_id(node, "p", NODE_PROGRAM, 0)
    state.step(nid)
    _require_type(node, NODE_PROGRAM, parent_id="root")
    _assert_keys(
        node,
        ("rules",),
        node_id=nid,
        allowed_extra=(
            "pre_rules",
            "post_rules",
            "default",
            PARENT_VARIABLES_KEY,
        ),
    )

    rules = node.get("rules")
    if not isinstance(rules, list):
        raise DslValidationError(
            detail="program.rules must be an array.",
            headers={"X-Node-Id": nid},
        )
    for index, rule in enumerate(rules):
        _validate_rule(
            rule,
            parent_id=nid,
            index=index,
            state=state,
            depth=1,
            context="rule",
        )

    # Sprint 7: pre_rules and post_rules are real now. Each entry is a
    # rule-shaped node, but the contained statements are restricted to
    # the section's allowed set (set_data/veto in pre, set_points/
    # set_case_name in post, set_callback_data in both).
    for section_key, ctx in (("pre_rules", "pre"), ("post_rules", "post")):
        section = node.get(section_key)
        if section is None:
            continue
        if not isinstance(section, list):
            raise DslValidationError(
                detail=f"program.{section_key} must be an array.",
                headers={"X-Node-Id": nid},
            )
        for index, rule in enumerate(section):
            _validate_rule(
                rule,
                parent_id=nid,
                index=index,
                state=state,
                depth=1,
                context=ctx,
            )

    # Sprint 7: parent_variables is an optional declarative override map
    # applied to a fresh copy of the parent built-in before its
    # calculate_points runs. Keys must be strings, values must be JSON
    # scalars (the registry-level "does this variable exist?" check
    # happens at create/update time in StrategyDefinitionService — here
    # we only enforce the AST shape).
    parent_vars = node.get(PARENT_VARIABLES_KEY)
    if parent_vars is not None:
        if not isinstance(parent_vars, dict):
            raise DslValidationError(
                detail=f"program.{PARENT_VARIABLES_KEY} must be an object.",
                headers={"X-Node-Id": nid},
            )
        for key, value in parent_vars.items():
            if not isinstance(key, str) or not key.startswith("variable_"):
                raise DslValidationError(
                    detail=(
                        f"program.{PARENT_VARIABLES_KEY} key '{key}' must "
                        "be a string starting with 'variable_'."
                    ),
                    headers={"X-Node-Id": nid},
                )
            if not isinstance(value, _LITERAL_TYPES) or isinstance(value, bytes):
                raise DslValidationError(
                    detail=(
                        f"program.{PARENT_VARIABLES_KEY}['{key}'] must be "
                        "a JSON scalar (string, number, boolean, or null)."
                    ),
                    headers={"X-Node-Id": nid},
                )

    default = node.get("default")
    if default is not None:
        _validate_statement(
            default,
            parent_id=nid,
            index=0,
            state=state,
            depth=1,
            context="default",
        )


def _validate_then(
    then: Any,
    *,
    parent_id: str,
    state: _State,
    depth: int,
    context: str,
    label: str,
) -> None:
    """Validate a statement-list body (a rule's then / else / else_if then).

    All three share the same contract: a non-empty list of statements,
    each validated in the surrounding section ``context``.
    """
    if not isinstance(then, list) or not then:
        raise DslValidationError(
            detail=f"{label} must be a non-empty array of statements.",
            headers={"X-Node-Id": parent_id},
        )
    for i, stmt in enumerate(then):
        _validate_statement(
            stmt,
            parent_id=parent_id,
            index=i,
            state=state,
            depth=depth + 1,
            context=context,
        )


def _validate_rule(
    node: Any,
    *,
    parent_id: str,
    index: int,
    state: _State,
    depth: int,
    context: str = "rule",
) -> None:
    """
    Validate a single ``rule`` node and its condition/branches.

    Args:
        node (Any): The rule AST node.
        parent_id (str): Id of the enclosing node, for error reporting.
        index (int): Position of this rule among its siblings.
        state (_State): Shared validation state (node/depth budgets).
        depth (int): Current nesting depth.
        context (str): Logical context label (e.g. ``"rule"``) controlling
            which constructs are allowed.

    Raises:
        DslValidationError: If the rule or any descendant is invalid.
    """
    if not isinstance(node, dict):
        raise DslValidationError(
            detail="program.rules[*] must be objects.",
            headers={"X-Node-Id": parent_id},
        )
    nid = _node_id(node, parent_id, NODE_RULE, index)
    state.step(nid)
    _require_type(node, NODE_RULE, parent_id=parent_id)
    _assert_keys(
        node,
        ("when", "then"),
        node_id=nid,
        allowed_extra=("else_if", "else"),
    )
    _check_depth(depth, nid, state)

    when = node["when"]
    _validate_condition(
        when,
        parent_id=nid,
        index=0,
        state=state,
        depth=depth + 1,
        context=context,
    )

    _validate_then(
        node.get("then"),
        parent_id=nid,
        state=state,
        depth=depth,
        context=context,
        label="rule.then",
    )

    # else_if / else share the rule's section context (a post-rule's else
    # branch is still a post-rule statement, etc.). They are optional; an
    # empty/missing list leaves the pre-else_if AST shape unchanged.
    else_if = node.get("else_if")
    if else_if is not None:
        if not isinstance(else_if, list):
            raise DslValidationError(
                detail="rule.else_if must be an array.",
                headers={"X-Node-Id": nid},
            )
        for j, branch in enumerate(else_if):
            branch_id = f"{nid}.else_if.{j}"
            state.step(branch_id)
            if not isinstance(branch, dict):
                raise DslValidationError(
                    detail="rule.else_if[*] must be objects.",
                    headers={"X-Node-Id": branch_id},
                )
            extras = set(branch.keys()) - {"when", "then", "id"}
            if extras:
                raise DslValidationError(
                    detail=(
                        f"rule.else_if[{j}] has unexpected keys: " f"{sorted(extras)}."
                    ),
                    headers={"X-Node-Id": branch_id},
                )
            if "when" not in branch:
                raise DslValidationError(
                    detail="rule.else_if[*] missing required key 'when'.",
                    headers={"X-Node-Id": branch_id},
                )
            _validate_condition(
                branch["when"],
                parent_id=branch_id,
                index=0,
                state=state,
                depth=depth + 1,
                context=context,
            )
            _validate_then(
                branch.get("then"),
                parent_id=branch_id,
                state=state,
                depth=depth,
                context=context,
                label="rule.else_if[*].then",
            )

    else_stmts = node.get("else")
    if else_stmts is not None:
        _validate_then(
            else_stmts,
            parent_id=nid,
            state=state,
            depth=depth,
            context=context,
            label="rule.else",
        )


def _validate_condition(
    node: Any,
    *,
    parent_id: str,
    index: int,
    state: _State,
    depth: int,
    context: str = "rule",
) -> None:
    """
    Validate a condition node (logical/comparison) and its operands.

    Args:
        node (Any): The condition AST node.
        parent_id (str): Id of the enclosing node, for error reporting.
        index (int): Position of this node among its siblings.
        state (_State): Shared validation state (node/depth budgets).
        depth (int): Current nesting depth.
        context (str): Logical context label controlling allowed constructs.

    Raises:
        DslValidationError: If the condition or any operand is invalid.
    """
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
                arg,
                parent_id=nid,
                index=i,
                state=state,
                depth=depth + 1,
                context=context,
            )
        return

    if ntype == NODE_NOT:
        _assert_keys(node, ("arg",), node_id=nid)
        _validate_condition(
            node["arg"],
            parent_id=nid,
            index=0,
            state=state,
            depth=depth + 1,
            context=context,
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
            node["left"],
            parent_id=nid,
            index=0,
            state=state,
            depth=depth + 1,
            context=context,
        )
        _validate_expression(
            node["right"],
            parent_id=nid,
            index=1,
            state=state,
            depth=depth + 1,
            context=context,
        )
        return

    # Conditions can be raw booleans/expressions too (literal true/false,
    # or a field that resolves to a number used as truthy). Delegate.
    _validate_expression(
        node,
        parent_id=parent_id,
        index=index,
        state=state,
        depth=depth,
        context=context,
    )


def _validate_expression(
    node: Any,
    *,
    parent_id: str,
    index: int,
    state: _State,
    depth: int,
    context: str = "rule",
) -> None:
    """
    Validate an expression node (field/literal/arith/func) and its children.

    Args:
        node (Any): The expression AST node.
        parent_id (str): Id of the enclosing node, for error reporting.
        index (int): Position of this node among its siblings.
        state (_State): Shared validation state (node/depth budgets).
        depth (int): Current nesting depth.
        context (str): Logical context label controlling allowed constructs.

    Raises:
        DslValidationError: If the expression or any sub-expression is invalid.
    """
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
                code="DSL_FIELD_PATH_NOT_ALLOWED",
                params={"nodeId": nid, "path": path},
            )
        # Sprint 7: parent.points / parent.case_name are only meaningful
        # inside post_rules — using them in main rules or pre_rules
        # would read uninitialised state. Reject early with a clear
        # message rather than letting the interpreter return None.
        if is_parent_field_path(path) and context != "post":
            raise DslValidationError(
                detail=(
                    f"field.path '{path}' is only available inside "
                    "post_rules (DSL_EXTEND mode)."
                ),
                headers={"X-Node-Id": nid},
                code="DSL_PARENT_FIELD_OUTSIDE_POST",
                params={"nodeId": nid, "path": path, "context": context},
            )
        return

    if ntype == NODE_ARITH:
        _assert_keys(node, ("op", "left", "right"), node_id=nid)
        op = node["op"]
        if op not in ALLOWED_ARITH_OPS:
            raise DslValidationError(
                detail=f"arith.op '{op}' is not allowed.",
                headers={"X-Node-Id": nid},
                code="DSL_ARITH_OP_NOT_ALLOWED",
                params={"nodeId": nid, "op": op},
            )
        _validate_expression(
            node["left"],
            parent_id=nid,
            index=0,
            state=state,
            depth=depth + 1,
            context=context,
        )
        _validate_expression(
            node["right"],
            parent_id=nid,
            index=1,
            state=state,
            depth=depth + 1,
            context=context,
        )
        return

    if ntype == NODE_FUNC_CALL:
        _assert_keys(node, ("name", "args"), node_id=nid)
        name = node["name"]
        if name not in ALLOWED_FUNC_NAMES:
            raise DslValidationError(
                detail=f"func_call.name '{name}' is not allowed.",
                headers={"X-Node-Id": nid},
                code="DSL_FUNC_NAME_NOT_ALLOWED",
                params={"nodeId": nid, "name": name},
            )
        args = node["args"]
        expected_arity = FUNC_ARITY[name]
        if not isinstance(args, list) or len(args) != expected_arity:
            actual = len(args) if isinstance(args, list) else "non-list"
            raise DslValidationError(
                detail=(
                    f"func_call '{name}' expects {expected_arity} args, "
                    f"got {actual}."
                ),
                headers={"X-Node-Id": nid},
                code="DSL_FUNC_ARITY_MISMATCH",
                params={
                    "nodeId": nid,
                    "name": name,
                    "expected": expected_arity,
                    "actual": actual,
                },
            )
        for i, arg in enumerate(args):
            _validate_expression(
                arg,
                parent_id=nid,
                index=i,
                state=state,
                depth=depth + 1,
                context=context,
            )
        return


def _validate_statement(
    node: Any,
    *,
    parent_id: str,
    index: int,
    state: _State,
    depth: int,
    context: str = "rule",
) -> None:
    """
    Validate a statement node (e.g. ``set``, ``emit``, ``return``).

    Args:
        node (Any): The statement AST node.
        parent_id (str): Id of the enclosing node, for error reporting.
        index (int): Position of this statement among its siblings.
        state (_State): Shared validation state (node/depth budgets).
        depth (int): Current nesting depth.
        context (str): Logical context label controlling allowed constructs.

    Raises:
        DslValidationError: If the statement or any sub-node is invalid.
    """
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
                    "(expected one of: "
                    + ", ".join(sorted(STATEMENT_NODE_TYPES))
                    + ")."
                ),
                headers={"X-Node-Id": parent_id},
            )
        raise DslValidationError(
            detail=f"Unknown statement node type: '{ntype}'.",
            headers={"X-Node-Id": parent_id},
        )
    # Sprint 7: enforce per-section statement whitelisting BEFORE any
    # shape validation so the error message points the designer at the
    # real problem ("you can't veto from a main rule") rather than a
    # generic structural mismatch downstream.
    allowed = STATEMENT_ALLOWED_CONTEXTS.get(ntype, set())
    if context not in allowed:
        raise DslValidationError(
            detail=(
                f"Statement '{ntype}' is not allowed inside "
                f"'{context}' section (allowed: {sorted(allowed)})."
            ),
            headers={"X-Node-Id": _node_id(node, parent_id, ntype, index)},
        )
    nid = _node_id(node, parent_id, ntype, index)
    state.step(nid)
    _check_depth(depth, nid, state)

    if ntype == NODE_ASSIGN_POINTS:
        _assert_keys(node, ("value", "case_name"), node_id=nid)
        _validate_expression(
            node["value"],
            parent_id=nid,
            index=0,
            state=state,
            depth=depth + 1,
            context=context,
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
            node["value"],
            parent_id=nid,
            index=0,
            state=state,
            depth=depth + 1,
            context=context,
        )
        return

    if ntype == NODE_SET_DATA:
        # Sprint 7: writes into the working_data dict passed to the
        # parent built-in. The interpreter mutates a copy of data, so
        # pre-rule mutations are local to this request.
        _assert_keys(node, ("key", "value"), node_id=nid)
        key = node["key"]
        if not isinstance(key, str) or not key:
            raise DslValidationError(
                detail="set_data.key must be a non-empty string.",
                headers={"X-Node-Id": nid},
            )
        # Keep the data namespace consistent with the field-path regex:
        # only alphanumeric + underscore, no dots/dashes.
        if not is_valid_data_path(f"data.{key}"):
            raise DslValidationError(
                detail=(
                    "set_data.key must match [A-Za-z0-9_]+ so it is "
                    "addressable via 'data.<key>' from the AST."
                ),
                headers={"X-Node-Id": nid},
            )
        _validate_expression(
            node["value"],
            parent_id=nid,
            index=0,
            state=state,
            depth=depth + 1,
            context=context,
        )
        return

    if ntype == NODE_VETO:
        # Sprint 7: halts the whole DSL_EXTEND pipeline (parent is NOT
        # invoked, post_rules are NOT run). Final result is
        # (0, case_name, current callback_data).
        _assert_keys(node, ("case_name",), node_id=nid)
        case_name = node["case_name"]
        if not is_valid_case_name(case_name):
            raise DslValidationError(
                detail=(
                    "veto.case_name must be 1-"
                    f"{CASE_NAME_MAX_LEN} printable ASCII characters."
                ),
                headers={"X-Node-Id": nid},
            )
        return

    if ntype == NODE_SET_POINTS:
        # Sprint 7: post-rule override of the parent's points. Unlike
        # assign_points (which halts the rule), set_points lets the
        # remaining statements in the post-rule keep running, so a
        # designer can chain set_points + set_callback_data.
        _assert_keys(node, ("value",), node_id=nid)
        _validate_expression(
            node["value"],
            parent_id=nid,
            index=0,
            state=state,
            depth=depth + 1,
            context=context,
        )
        return

    if ntype == NODE_SET_CASE_NAME:
        # Sprint 7: post-rule override of the parent's caseName. The
        # value is an expression so it can be computed (e.g. a literal
        # text block, or even derived from data.* — though the latter
        # is unusual). The runtime checks the resolved value is a
        # printable ASCII string.
        _assert_keys(node, ("value",), node_id=nid)
        _validate_expression(
            node["value"],
            parent_id=nid,
            index=0,
            state=state,
            depth=depth + 1,
            context=context,
        )
        return

    if ntype == NODE_RETURN:
        _assert_keys(node, (), node_id=nid)
        return


def _check_depth(depth: int, node_id: str, state: _State) -> None:
    """
    Enforce the maximum AST nesting depth.

    Args:
        depth (int): Current nesting depth.
        node_id (str): Id of the node being visited (reported on error).
        state (_State): Validation state carrying ``max_depth``.

    Raises:
        DslValidationError: If ``depth`` exceeds ``state.max_depth``.
    """
    if depth > state.max_depth:
        raise DslValidationError(
            detail=(
                f"AST nesting depth exceeds the maximum allowed "
                f"({state.max_depth})."
            ),
            headers={"X-Node-Id": node_id},
        )
