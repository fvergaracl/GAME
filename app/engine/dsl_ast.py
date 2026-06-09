"""
AST node definitions and the field-access whitelist for the strategy DSL.

This module is pure data + small pure helpers - no I/O, no service
dependencies, no async. It is imported by the validator, the interpreter,
and the execution context. Keeping it dependency-free is what allows the
adversarial test suite to import the whitelist directly and assert on it
without spinning up the rest of the app.

Two pieces live here:

1. The grammar of allowed nodes: ``NODE_*`` constants plus the operator
   whitelists used by ``compare`` and ``arith`` nodes.

2. The ``FIELD_RESOLVERS`` map - the only legal targets of a ``field``
   node's ``path``. Anything outside this map (or the ``data.<key>``
   prefix) is rejected at validation time, not at runtime. This is what
   keeps a malicious tenant from writing ``{"type":"field","path":"__builtins__"}``
   and getting an interpreter handler to evaluate it.

The ``data.*`` namespace is open - keys are arbitrary because callers
supply ``data`` per-event - but the resolver only snapshots scalar values
from the request payload, never live attribute lookups.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional, Set, Tuple

# Node types ----------------------------------------------------------------
# The handler tables in dsl_validator and dsl_interpreter dispatch on these
# strings. Adding a node here without adding a handler will be caught by the
# validator (unknown type) - the constants are intentionally exhaustive.

NODE_PROGRAM = "program"
# A rule node carries ``when`` (condition) + ``then`` (statement list) and,
# optionally, ``else_if`` (a list of ``{when, then}`` branch objects) and
# ``else`` (a statement list). The interpreter evaluates the base ``when``,
# then each ``else_if`` in order, and finally ``else`` if nothing matched.
# The else_if branches are plain objects, not typed nodes, so no new node
# type is needed. Both extra keys are omitted when empty.
NODE_RULE = "rule"

NODE_AND = "and"
NODE_OR = "or"
NODE_NOT = "not"
NODE_COMPARE = "compare"

NODE_LITERAL = "literal"
NODE_FIELD = "field"
NODE_ARITH = "arith"
# Sprint 6: dedicated node for non-binary built-ins (unary ``int``,
# ternary ``clamp``). Binary ``min`` / ``max`` stay in ``arith`` because
# they fit the existing left/right dispatch table cleanly.
NODE_FUNC_CALL = "func_call"

NODE_ASSIGN_POINTS = "assign_points"
NODE_SET_CALLBACK_DATA = "set_callback_data"
NODE_RETURN = "return"

# Sprint 7: statements for DSL_EXTEND mode (pre_rules / post_rules).
# - set_data + veto are pre-only (they affect what the parent sees / whether
#   it runs at all).
# - set_points + set_case_name are post-only (they mutate the parent's result).
# The context whitelist below (STATEMENT_ALLOWED_CONTEXTS) is what the
# validator consults to reject misplaced statements; the interpreter has
# matching dispatch entries.
NODE_SET_DATA = "set_data"
NODE_VETO = "veto"
NODE_SET_POINTS = "set_points"
NODE_SET_CASE_NAME = "set_case_name"


ALL_NODE_TYPES: Set[str] = {
    NODE_PROGRAM,
    NODE_RULE,
    NODE_AND,
    NODE_OR,
    NODE_NOT,
    NODE_COMPARE,
    NODE_LITERAL,
    NODE_FIELD,
    NODE_ARITH,
    NODE_FUNC_CALL,
    NODE_ASSIGN_POINTS,
    NODE_SET_CALLBACK_DATA,
    NODE_RETURN,
    NODE_SET_DATA,
    NODE_VETO,
    NODE_SET_POINTS,
    NODE_SET_CASE_NAME,
}

CONDITION_NODE_TYPES: Set[str] = {
    NODE_AND,
    NODE_OR,
    NODE_NOT,
    NODE_COMPARE,
    NODE_LITERAL,
    NODE_FIELD,
}

EXPRESSION_NODE_TYPES: Set[str] = {
    NODE_LITERAL,
    NODE_FIELD,
    NODE_ARITH,
    NODE_FUNC_CALL,
}

STATEMENT_NODE_TYPES: Set[str] = {
    NODE_ASSIGN_POINTS,
    NODE_SET_CALLBACK_DATA,
    NODE_RETURN,
    NODE_SET_DATA,
    NODE_VETO,
    NODE_SET_POINTS,
    NODE_SET_CASE_NAME,
}


# Sprint 7: which statements are allowed inside which AST section.
# Context strings: "rule" (main rules[]), "default" (program.default),
# "pre" (program.pre_rules[]), "post" (program.post_rules[]).
#
# IMPORTANT: dashboard/src/views/strategies/dsl/whitelists.js mirrors
# this map for client-side validation - keep them in sync.
STATEMENT_ALLOWED_CONTEXTS: Dict[str, Set[str]] = {
    NODE_ASSIGN_POINTS: {"rule", "default"},
    NODE_SET_CALLBACK_DATA: {"rule", "default", "pre", "post"},
    NODE_RETURN: {"rule", "default", "pre", "post"},
    NODE_SET_DATA: {"pre"},
    NODE_VETO: {"pre"},
    NODE_SET_POINTS: {"post"},
    NODE_SET_CASE_NAME: {"post"},
}


ALLOWED_COMPARE_OPS: Set[str] = {"<", "<=", "==", "!=", ">=", ">"}
# Sprint 6: ``min`` / ``max`` added as binary arith ops so they reuse the
# existing _ARITH_HANDLERS table. Unary ``int`` and ternary ``clamp`` are
# expressed through ``NODE_FUNC_CALL`` instead.
ALLOWED_ARITH_OPS: Set[str] = {"+", "-", "*", "/", "min", "max"}

# Whitelist of non-binary built-ins addressable through ``NODE_FUNC_CALL``.
# Keeping the arity explicit so the validator can reject bad call shapes
# without consulting the interpreter handler table.
# IMPORTANT: dashboard/src/views/strategies/dsl/whitelists.js mirrors
# this set for client-side validation - keep them in sync.
ALLOWED_FUNC_NAMES: Set[str] = {"int", "clamp"}
FUNC_ARITY: Dict[str, int] = {"int": 1, "clamp": 3}

# Sprint 7: program may carry pre_rules and post_rules (DSL_EXTEND mode).
# The validator now treats both as optional-but-can-be-non-empty lists of
# rule-shaped nodes; Sprint 6 used to require they be empty.
RESERVED_PROGRAM_KEYS: Set[str] = {"pre_rules", "post_rules"}

# Sprint 7: declarative override map applied to a fresh copy of the
# parent built-in before its calculate_points runs. Keys must be present
# in ``parent.get_variables()`` (validated against the registry at
# create/update time, see strategy_definition_service); values must be
# JSON scalars. Lives under ``program.parent_variables``.
PARENT_VARIABLES_KEY = "parent_variables"


# Field whitelist -----------------------------------------------------------

DATA_FIELD_PREFIX = "data."
_DATA_KEY_RE = re.compile(r"^[A-Za-z0-9_]+$")

# case_name lives in the response and gets bucketed by analytics; constrain
# it to printable ASCII without control bytes. 200 chars matches the
# strategy `name` cap so dashboards don't have to special-case it.
CASE_NAME_MAX_LEN = 200
_CASE_NAME_RE = re.compile(r"^[\x20-\x7E]{1,200}$")


@dataclass(frozen=True)
class FieldResolution:
    """How to obtain the value of a whitelisted ``field.path`` at runtime."""

    path: str
    kind: str  # "static" or "analytics"
    method: Optional[str] = None
    arg_fn: Optional[Callable[[Any], Tuple[Any, ...]]] = None


def _static(path: str, getter: Callable[[Any], Any]) -> Tuple[str, FieldResolution]:
    """
    Build a ``(path, FieldResolution)`` entry for a static field.

    Static fields are read directly off the context (no analytics call).

    Args:
        path (str): The whitelisted field path (e.g. ``"externalGameId"``).
        getter (Callable): Function extracting the value from the context.

    Returns:
        tuple: ``(path, FieldResolution)`` for inclusion in
        :data:`FIELD_RESOLVERS`.
    """
    return path, FieldResolution(path=path, kind="static", method=None, arg_fn=getter)


def _analytics(
    path: str, method: str, arg_fn: Callable[[Any], Tuple[Any, ...]]
) -> Tuple[str, FieldResolution]:
    """
    Build a ``(path, FieldResolution)`` entry for an analytics-backed field.

    Analytics fields are resolved by calling ``method`` on the analytics
    service with positional args produced by ``arg_fn``.

    Args:
        path (str): The whitelisted field path.
        method (str): Name of the analytics-service method to invoke.
        arg_fn (Callable): Builds the positional-args tuple from the context.

    Returns:
        tuple: ``(path, FieldResolution)`` for inclusion in
        :data:`FIELD_RESOLVERS`.
    """
    return path, FieldResolution(
        path=path, kind="analytics", method=method, arg_fn=arg_fn
    )


# The ``arg_fn`` builds the positional tuple passed to the analytics method,
# reading off a context object that exposes externalGameId/TaskId/UserId.
# We pass a tiny namespace (not the full ExecutionContext) to keep this map
# import-safe and side-effect free.

FIELD_RESOLVERS: Dict[str, FieldResolution] = dict(
    [
        _static(
            "externalGameId",
            lambda ctx: ctx.externalGameId,
        ),
        _static(
            "externalTaskId",
            lambda ctx: ctx.externalTaskId,
        ),
        _static(
            "externalUserId",
            lambda ctx: ctx.externalUserId,
        ),
        _analytics(
            "user.measurements_count",
            "get_user_task_measurements_count",
            lambda ctx: (ctx.externalTaskId, ctx.externalUserId),
        ),
        # Sprint 6: rolling-window count used by ``constantEffortStrategy``.
        # The window in seconds is currently hard-coded to 300 (5 minutes,
        # the strategy's default). Parametrising the window per-AST requires
        # variable substitution support which lands in Sprint 7.
        _analytics(
            "user.recent_measurements_count",
            "get_user_task_measurements_count_the_last_seconds",
            lambda ctx: (ctx.externalTaskId, ctx.externalUserId, 300),
        ),
        _analytics(
            "task.measurements_count",
            "count_measurements_by_external_task_id",
            lambda ctx: (ctx.externalTaskId,),
        ),
        _analytics(
            "user.avg_time",
            "get_avg_time_between_tasks_by_user_and_game_task",
            lambda ctx: (ctx.externalGameId, ctx.externalTaskId, ctx.externalUserId),
        ),
        _analytics(
            "all.avg_time",
            "get_avg_time_between_tasks_for_all_users",
            lambda ctx: (ctx.externalGameId, ctx.externalTaskId),
        ),
        _analytics(
            "user.last_window_diff",
            "get_last_window_time_diff",
            lambda ctx: (ctx.externalTaskId, ctx.externalUserId),
        ),
        _analytics(
            "user.new_last_window_diff",
            "get_new_last_window_time_diff",
            lambda ctx: (ctx.externalTaskId, ctx.externalUserId, ctx.externalGameId),
        ),
    ]
)


# Sprint 7: paths exposed only inside ``post_rules`` - they carry the
# parent built-in's result after the pre→parent→post pipeline. They are
# NOT in FIELD_RESOLVERS because their value is injected directly into
# ExecutionContext.resolved_fields by ``DslStrategy`` after the parent
# call, not eagerly precomputed alongside analytics fields.
PARENT_FIELD_PATHS: Set[str] = {"parent.points", "parent.case_name"}


def is_valid_data_path(path: str) -> bool:
    """``data.<key>`` where ``<key>`` is ``[A-Za-z0-9_]+``."""
    if not path.startswith(DATA_FIELD_PREFIX):
        return False
    suffix = path[len(DATA_FIELD_PREFIX) :]
    return bool(_DATA_KEY_RE.match(suffix))


def is_parent_field_path(path: str) -> bool:
    """``parent.points`` / ``parent.case_name`` - only valid in post_rules."""
    return path in PARENT_FIELD_PATHS


def is_known_field_path(path: str) -> bool:
    """Either a whitelisted analytic/static path, a parent.* path (Sprint 7,
    context-restricted by validator), or a well-formed data.* key."""
    return (
        path in FIELD_RESOLVERS
        or is_parent_field_path(path)
        or is_valid_data_path(path)
    )


def is_valid_case_name(value: Any) -> bool:
    """
    Return whether ``value`` is a syntactically valid case name.

    A valid case name is a string matching the case-name pattern
    (``_CASE_NAME_RE``).

    Args:
        value (Any): Candidate value to check.

    Returns:
        bool: ``True`` if ``value`` is a well-formed case name.
    """
    return isinstance(value, str) and bool(_CASE_NAME_RE.match(value))


# Field enumeration ---------------------------------------------------------
# ExecutionContext uses this to build a precompute list. It walks the AST
# permissively (will not raise on unknown nodes - that is the validator's
# job) so the same code path is safe to call after validation has passed.


def enumerate_field_paths(ast: Any) -> Set[str]:
    """Return every ``path`` referenced by a ``field`` node anywhere in the tree."""
    out: Set[str] = set()
    _walk_collect(ast, out)
    return out


def _walk_collect(node: Any, acc: Set[str]) -> None:
    """
    Recursively collect every ``field`` node ``path`` into ``acc``.

    Walks dicts and lists permissively (never raising on unknown nodes), so it
    is safe to run before or after validation.

    Args:
        node (Any): Current AST node (dict, list or scalar).
        acc (Set[str]): Accumulator mutated in place with discovered paths.
    """
    if isinstance(node, dict):
        if node.get("type") == NODE_FIELD:
            path = node.get("path")
            if isinstance(path, str):
                acc.add(path)
        for value in node.values():
            _walk_collect(value, acc)
    elif isinstance(node, list):
        for item in node:
            _walk_collect(item, acc)


def iter_program_rules(program: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """Iterate the ``rules`` list, tolerating a missing key (returns empty)."""
    rules = program.get("rules") if isinstance(program, dict) else None
    if isinstance(rules, list):
        return rules
    return []
