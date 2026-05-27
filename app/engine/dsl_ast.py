"""
AST node definitions and the field-access whitelist for the strategy DSL.

This module is pure data + small pure helpers — no I/O, no service
dependencies, no async. It is imported by the validator, the interpreter,
and the execution context. Keeping it dependency-free is what allows the
adversarial test suite to import the whitelist directly and assert on it
without spinning up the rest of the app.

Two pieces live here:

1. The grammar of allowed nodes: ``NODE_*`` constants plus the operator
   whitelists used by ``compare`` and ``arith`` nodes.

2. The ``FIELD_RESOLVERS`` map — the only legal targets of a ``field``
   node's ``path``. Anything outside this map (or the ``data.<key>``
   prefix) is rejected at validation time, not at runtime. This is what
   keeps a malicious tenant from writing ``{"type":"field","path":"__builtins__"}``
   and getting an interpreter handler to evaluate it.

The ``data.*`` namespace is open — keys are arbitrary because callers
supply ``data`` per-event — but the resolver only snapshots scalar values
from the request payload, never live attribute lookups.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional, Set, Tuple


# Node types ----------------------------------------------------------------
# The handler tables in dsl_validator and dsl_interpreter dispatch on these
# strings. Adding a node here without adding a handler will be caught by the
# validator (unknown type) — the constants are intentionally exhaustive.

NODE_PROGRAM = "program"
NODE_RULE = "rule"

NODE_AND = "and"
NODE_OR = "or"
NODE_NOT = "not"
NODE_COMPARE = "compare"

NODE_LITERAL = "literal"
NODE_FIELD = "field"
NODE_ARITH = "arith"

NODE_ASSIGN_POINTS = "assign_points"
NODE_SET_CALLBACK_DATA = "set_callback_data"
NODE_RETURN = "return"


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
    NODE_ASSIGN_POINTS,
    NODE_SET_CALLBACK_DATA,
    NODE_RETURN,
}

CONDITION_NODE_TYPES: Set[str] = {
    NODE_AND, NODE_OR, NODE_NOT, NODE_COMPARE, NODE_LITERAL, NODE_FIELD,
}

EXPRESSION_NODE_TYPES: Set[str] = {
    NODE_LITERAL, NODE_FIELD, NODE_ARITH,
}

STATEMENT_NODE_TYPES: Set[str] = {
    NODE_ASSIGN_POINTS, NODE_SET_CALLBACK_DATA, NODE_RETURN,
}


ALLOWED_COMPARE_OPS: Set[str] = {"<", "<=", "==", "!=", ">=", ">"}
ALLOWED_ARITH_OPS: Set[str] = {"+", "-", "*", "/"}

# Reserved for Sprint 7. The validator allows the keys to exist (empty
# arrays only) so a forward-compatible Blockly export does not break.
RESERVED_PROGRAM_KEYS: Set[str] = {"pre_rules", "post_rules"}


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
    return path, FieldResolution(path=path, kind="static", method=None, arg_fn=getter)


def _analytics(
    path: str, method: str, arg_fn: Callable[[Any], Tuple[Any, ...]]
) -> Tuple[str, FieldResolution]:
    return path, FieldResolution(
        path=path, kind="analytics", method=method, arg_fn=arg_fn
    )


# The ``arg_fn`` builds the positional tuple passed to the analytics method,
# reading off a context object that exposes externalGameId/TaskId/UserId.
# We pass a tiny namespace (not the full ExecutionContext) to keep this map
# import-safe and side-effect free.

FIELD_RESOLVERS: Dict[str, FieldResolution] = dict([
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
])


def is_valid_data_path(path: str) -> bool:
    """``data.<key>`` where ``<key>`` is ``[A-Za-z0-9_]+``."""
    if not path.startswith(DATA_FIELD_PREFIX):
        return False
    suffix = path[len(DATA_FIELD_PREFIX):]
    return bool(_DATA_KEY_RE.match(suffix))


def is_known_field_path(path: str) -> bool:
    """Either a whitelisted analytic/static path or a well-formed data.* key."""
    return path in FIELD_RESOLVERS or is_valid_data_path(path)


def is_valid_case_name(value: Any) -> bool:
    return isinstance(value, str) and bool(_CASE_NAME_RE.match(value))


# Field enumeration ---------------------------------------------------------
# ExecutionContext uses this to build a precompute list. It walks the AST
# permissively (will not raise on unknown nodes — that is the validator's
# job) so the same code path is safe to call after validation has passed.


def enumerate_field_paths(ast: Any) -> Set[str]:
    """Return every ``path`` referenced by a ``field`` node anywhere in the tree."""
    out: Set[str] = set()
    _walk_collect(ast, out)
    return out


def _walk_collect(node: Any, acc: Set[str]) -> None:
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
