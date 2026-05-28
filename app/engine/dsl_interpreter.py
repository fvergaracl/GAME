"""
Walker-based interpreter for the strategy DSL.

This is the sandbox. It walks the JSON AST node-by-node, dispatching on
``node["type"]`` through a fixed handler table — no ``getattr``, no
``eval``, no ``exec``. Anything not in the handler table is rejected as
``DslValidationError`` (the validator should have caught it; the runtime
check is defence in depth).

Hard guarantees:

* No code path exposes Python attribute lookup to AST-supplied strings.
* Field access is a frozen-dict lookup; the resolved values were
  precomputed by ``ExecutionContext.build_for_ast``.
* Node count and recursion depth are bounded — the validator already
  rejects programs that would exceed them; the runtime guards exist so
  that future dynamic expansion (e.g. macros) still can't blow out.
* ``await asyncio.sleep(0)`` every ``yield_every`` visits gives the
  event loop a chance to actually cancel the coroutine when
  ``asyncio.wait_for`` fires. Without it a CPU-bound walk would run to
  completion and only *then* see the timeout — which is what
  ``RestrictedPython``-style sandboxes generally get wrong.

Execution semantics mirror ``app/engine/default.py``:

* Rules are evaluated in order.
* The first ``assign_points`` reached in a matched rule sets the result
  and halts the program (early-return). ``set_callback_data`` statements
  before the assignment accumulate into a dict; statements after the
  assignment never run.
* If no rule matches, the program's ``default`` section runs (if any);
  otherwise the result is ``(0, None, {})``.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, TypedDict

from app.core.exceptions import (
    DslExecutionError,
    DslLimitExceededError,
    DslValidationError,
)
from app.engine.dsl_ast import (
    ALLOWED_ARITH_OPS,
    ALLOWED_COMPARE_OPS,
    ALLOWED_FUNC_NAMES,
    FUNC_ARITY,
    NODE_AND,
    NODE_ARITH,
    NODE_ASSIGN_POINTS,
    NODE_COMPARE,
    NODE_FIELD,
    NODE_FUNC_CALL,
    NODE_LITERAL,
    NODE_NOT,
    NODE_OR,
    NODE_RETURN,
    NODE_SET_CALLBACK_DATA,
    NODE_SET_CASE_NAME,
    NODE_SET_DATA,
    NODE_SET_POINTS,
    NODE_VETO,
)
from app.engine.dsl_execution_context import ExecutionContext


class DslExecutionResult(TypedDict, total=False):
    points: float
    case_name: Optional[str]
    callback_data: Dict[str, Any]
    trace: List[Dict[str, Any]]
    # Sprint 7: DSL_EXTEND-only outputs. ``working_data`` is the dict
    # that pre-rules mutated via set_data — the orchestrator hands it
    # to the parent built-in. ``vetoed`` signals that a pre-rule veto
    # fired so the orchestrator skips parent + post entirely.
    working_data: Dict[str, Any]
    vetoed: bool


class _DslHalt(Exception):
    """Internal sentinel raised when an ``assign_points`` short-circuits."""


class DslInterpreter:
    def __init__(
        self,
        *,
        max_nodes: int,
        max_depth: int,
        yield_every: int = 64,
    ) -> None:
        self._max_nodes = max_nodes
        self._max_depth = max_depth
        self._yield_every = max(yield_every, 1)

    async def execute(
        self,
        ast: Dict[str, Any],
        ctx: ExecutionContext,
        *,
        mode: str = "full",
        initial_data: Optional[Dict[str, Any]] = None,
        parent_result: Optional[Dict[str, Any]] = None,
    ) -> DslExecutionResult:
        """
        Walk ``ast`` to completion and return the result.

        ``mode`` selects which section of the program runs:

        * ``"full"`` — main ``rules`` + ``default`` (DSL_FULL behaviour;
          this is the unchanged Sprint 5 path).
        * ``"pre"`` — only ``pre_rules`` (DSL_EXTEND phase 1). The
          ``initial_data`` dict is cloned into ``state.working_data`` so
          ``set_data`` statements can mutate it; the orchestrator
          (``DslStrategy``) reads ``state.working_data`` back out to
          pass to the parent built-in.
        * ``"post"`` — only ``post_rules`` (DSL_EXTEND phase 3). The
          ``parent_result`` dict bootstraps the run state (points,
          case_name, callback_data) so ``set_points`` /
          ``set_case_name`` / ``set_callback_data`` mutate from the
          parent's output as the starting point. The corresponding
          ``parent.points`` / ``parent.case_name`` field paths are
          expected to be already present in ``ctx.resolved_fields``
          (injected by ``ExecutionContext.build_for_ast``).
        """
        state = _RunState()
        if initial_data is not None:
            # Shallow copy is intentional: set_data only writes scalars
            # via expression evaluation. Nested mutation is not part of
            # the AST grammar.
            state.working_data = dict(initial_data)
        if parent_result is not None:
            state.points = float(parent_result.get("points") or 0)
            state.case_name = parent_result.get("case_name")
            state.callback_data = dict(
                parent_result.get("callback_data") or {}
            )
            state.matched = True
        try:
            await self._run_program(ast, ctx, state, mode=mode)
        except _DslHalt:
            pass

        return {
            "points": state.points if state.matched else 0,
            "case_name": state.case_name,
            "callback_data": state.callback_data,
            "trace": state.trace,
            # Sprint 7 outputs. They are no-ops for DSL_FULL callers
            # (working_data stays empty, vetoed stays False) so the
            # existing Sprint 5 contract is unchanged.
            "working_data": state.working_data,
            "vetoed": state.vetoed,
        }

    # ----- top-level dispatch ----------------------------------------------

    async def _run_program(
        self,
        node: Dict[str, Any],
        ctx: ExecutionContext,
        state: _RunState,
        *,
        mode: str = "full",
    ) -> None:
        self._step(state, node)

        if mode == "full":
            for rule in node.get("rules") or []:
                await self._run_rule(rule, ctx, state, depth=1)

            default = node.get("default")
            if default is not None and not state.matched:
                await self._run_statement(default, ctx, state, depth=1)
            return

        # Sprint 7: DSL_EXTEND phases. ``pre`` and ``post`` walk a
        # distinct section of the program and ignore the others — the
        # main ``rules`` + ``default`` are exclusively the DSL_FULL
        # path. This keeps the two execution models from accidentally
        # mixing state ("set_data" leaking into a DSL_FULL run, etc.).
        section_key = "pre_rules" if mode == "pre" else "post_rules"
        for rule in node.get(section_key) or []:
            await self._run_rule(rule, ctx, state, depth=1)

    async def _run_rule(
        self,
        node: Dict[str, Any],
        ctx: ExecutionContext,
        state: _RunState,
        *,
        depth: int,
    ) -> None:
        self._step(state, node)
        self._check_depth(depth, node)

        # if / else-if / else cascade. The base branch (``when``/``then``)
        # is evaluated first; if it matches, ``then`` runs and the rule
        # ends. Otherwise each ``else_if`` branch is tried in order, and the
        # first whose condition is truthy runs its ``then`` and ends the
        # rule. If none match and an ``else`` body exists, it runs. This
        # only decides which statement stack runs inside the rule — the
        # program-level rule chaining and ``default`` are unchanged (a
        # non-halting branch still falls through to the next rule).
        matched = await self._eval_condition(
            node["when"], ctx, state, depth=depth + 1
        )
        if matched:
            state.trace.append(
                {
                    "nodeId": node.get("id"),
                    "type": "rule",
                    "value": True,
                    "branch": "match",
                }
            )
            await self._run_branch(
                node.get("then"), ctx, state, depth=depth + 1
            )
            return

        for i, branch in enumerate(node.get("else_if") or []):
            self._step(state, branch)
            branch_matched = await self._eval_condition(
                branch["when"], ctx, state, depth=depth + 1
            )
            if branch_matched:
                state.trace.append(
                    {
                        "nodeId": node.get("id"),
                        "type": "rule",
                        "value": True,
                        "branch": f"elseif:{i}",
                    }
                )
                await self._run_branch(
                    branch.get("then"), ctx, state, depth=depth + 1
                )
                return

        else_stmts = node.get("else")
        if else_stmts:
            state.trace.append(
                {
                    "nodeId": node.get("id"),
                    "type": "rule",
                    "value": False,
                    "branch": "else",
                }
            )
            await self._run_branch(else_stmts, ctx, state, depth=depth + 1)
            return

        state.trace.append(
            {
                "nodeId": node.get("id"),
                "type": "rule",
                "value": False,
                "branch": "skip",
            }
        )

    async def _run_branch(
        self,
        statements: Optional[List[Dict[str, Any]]],
        ctx: ExecutionContext,
        state: _RunState,
        *,
        depth: int,
    ) -> None:
        for stmt in statements or []:
            await self._run_statement(stmt, ctx, state, depth=depth)

    # ----- statements ------------------------------------------------------

    async def _run_statement(
        self,
        node: Dict[str, Any],
        ctx: ExecutionContext,
        state: _RunState,
        *,
        depth: int,
    ) -> None:
        await self._maybe_yield(state)
        self._step(state, node)
        self._check_depth(depth, node)

        ntype = node.get("type")
        if ntype == NODE_ASSIGN_POINTS:
            value = await self._eval_expression(
                node["value"], ctx, state, depth=depth + 1
            )
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise DslExecutionError(
                    detail="assign_points.value must evaluate to a number.",
                    headers={"X-Node-Id": str(node.get("id"))},
                    code="DSL_ASSIGN_POINTS_NOT_NUMBER",
                    params={
                        "nodeId": node.get("id"),
                        "actualType": type(value).__name__,
                    },
                )
            state.points = value
            state.case_name = node["case_name"]
            state.matched = True
            state.trace.append(
                {
                    "nodeId": node.get("id"),
                    "type": ntype,
                    "value": value,
                    "branch": "match",
                }
            )
            raise _DslHalt()

        if ntype == NODE_SET_CALLBACK_DATA:
            value = await self._eval_expression(
                node["value"], ctx, state, depth=depth + 1
            )
            state.callback_data[node["key"]] = value
            state.trace.append(
                {
                    "nodeId": node.get("id"),
                    "type": ntype,
                    "value": value,
                }
            )
            return

        # Sprint 7: DSL_EXTEND pre-rule statements. set_data writes into
        # ``state.working_data`` — the dict the orchestrator hands to the
        # parent built-in's ``calculate_points``. veto raises _DslHalt
        # with state.vetoed=True so the orchestrator skips both the
        # parent call and the entire post_rules phase.
        if ntype == NODE_SET_DATA:
            value = await self._eval_expression(
                node["value"], ctx, state, depth=depth + 1
            )
            state.working_data[node["key"]] = value
            state.trace.append(
                {
                    "nodeId": node.get("id"),
                    "type": ntype,
                    "value": value,
                }
            )
            return

        if ntype == NODE_VETO:
            state.points = 0
            state.case_name = node["case_name"]
            state.matched = True
            state.vetoed = True
            state.trace.append(
                {
                    "nodeId": node.get("id"),
                    "type": ntype,
                    "value": node["case_name"],
                    "branch": "veto",
                }
            )
            raise _DslHalt()

        # Sprint 7: DSL_EXTEND post-rule statements. set_points mutates
        # ``state.points`` WITHOUT halting (unlike assign_points) so a
        # designer can chain set_points + set_callback_data inside a
        # single post-rule. set_case_name overrides the caseName
        # accumulated from the parent.
        if ntype == NODE_SET_POINTS:
            value = await self._eval_expression(
                node["value"], ctx, state, depth=depth + 1
            )
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise DslExecutionError(
                    detail="set_points.value must evaluate to a number.",
                    headers={"X-Node-Id": str(node.get("id"))},
                    code="DSL_SET_POINTS_NOT_NUMBER",
                    params={
                        "nodeId": node.get("id"),
                        "actualType": type(value).__name__,
                    },
                )
            state.points = value
            state.matched = True
            state.trace.append(
                {
                    "nodeId": node.get("id"),
                    "type": ntype,
                    "value": value,
                }
            )
            return

        if ntype == NODE_SET_CASE_NAME:
            value = await self._eval_expression(
                node["value"], ctx, state, depth=depth + 1
            )
            if not isinstance(value, str):
                raise DslExecutionError(
                    detail=(
                        "set_case_name.value must evaluate to a string."
                    ),
                    headers={"X-Node-Id": str(node.get("id"))},
                    code="DSL_SET_CASE_NAME_NOT_STRING",
                    params={
                        "nodeId": node.get("id"),
                        "actualType": type(value).__name__,
                    },
                )
            state.case_name = value
            state.matched = True
            state.trace.append(
                {
                    "nodeId": node.get("id"),
                    "type": ntype,
                    "value": value,
                }
            )
            return

        if ntype == NODE_RETURN:
            state.trace.append(
                {
                    "nodeId": node.get("id"),
                    "type": ntype,
                    "value": None,
                    "branch": "halt",
                }
            )
            raise _DslHalt()

        raise DslValidationError(
            detail=f"Unknown statement node type: '{ntype}'.",
            headers={"X-Node-Id": str(node.get("id"))},
            code="DSL_UNKNOWN_STATEMENT",
            params={"nodeId": node.get("id"), "nodeType": ntype},
        )

    # ----- conditions ------------------------------------------------------

    async def _eval_condition(
        self,
        node: Dict[str, Any],
        ctx: ExecutionContext,
        state: _RunState,
        *,
        depth: int,
    ) -> bool:
        await self._maybe_yield(state)
        self._step(state, node)
        self._check_depth(depth, node)

        ntype = node.get("type")
        if ntype == NODE_AND:
            for i, arg in enumerate(node["args"]):
                ok = await self._eval_condition(
                    arg, ctx, state, depth=depth + 1
                )
                if not ok:
                    # Record the remaining args as skipped so the trace
                    # explains why the AND failed.
                    state.trace.append(
                        {
                            "nodeId": node.get("id"),
                            "type": ntype,
                            "value": False,
                            "branch": f"short_circuit:{i}",
                        }
                    )
                    return False
            state.trace.append(
                {"nodeId": node.get("id"), "type": ntype, "value": True}
            )
            return True

        if ntype == NODE_OR:
            for i, arg in enumerate(node["args"]):
                ok = await self._eval_condition(
                    arg, ctx, state, depth=depth + 1
                )
                if ok:
                    state.trace.append(
                        {
                            "nodeId": node.get("id"),
                            "type": ntype,
                            "value": True,
                            "branch": f"short_circuit:{i}",
                        }
                    )
                    return True
            state.trace.append(
                {"nodeId": node.get("id"), "type": ntype, "value": False}
            )
            return False

        if ntype == NODE_NOT:
            value = await self._eval_condition(
                node["arg"], ctx, state, depth=depth + 1
            )
            state.trace.append(
                {"nodeId": node.get("id"), "type": ntype, "value": not value}
            )
            return not value

        if ntype == NODE_COMPARE:
            left = await self._eval_expression(
                node["left"], ctx, state, depth=depth + 1
            )
            right = await self._eval_expression(
                node["right"], ctx, state, depth=depth + 1
            )
            op = node["op"]
            if op not in ALLOWED_COMPARE_OPS:
                raise DslValidationError(
                    detail=f"compare.op '{op}' is not allowed.",
                    headers={"X-Node-Id": str(node.get("id"))},
                    code="DSL_COMPARE_OP_NOT_ALLOWED",
                    params={"nodeId": node.get("id"), "op": op},
                )
            try:
                result = _apply_compare(op, left, right)
            except TypeError as exc:
                raise DslExecutionError(
                    detail=(
                        f"compare {op!r} between incompatible types "
                        f"{type(left).__name__} and {type(right).__name__}."
                    ),
                    headers={"X-Node-Id": str(node.get("id"))},
                    code="DSL_COMPARE_TYPE_MISMATCH",
                    params={
                        "nodeId": node.get("id"),
                        "op": op,
                        "leftType": type(left).__name__,
                        "rightType": type(right).__name__,
                    },
                ) from exc
            state.trace.append(
                {"nodeId": node.get("id"), "type": ntype, "value": result}
            )
            return result

        # Allow bare expressions as conditions (literal true, field >= 1, etc).
        value = await self._eval_expression(node, ctx, state, depth=depth)
        return bool(value)

    # ----- expressions -----------------------------------------------------

    async def _eval_expression(
        self,
        node: Dict[str, Any],
        ctx: ExecutionContext,
        state: _RunState,
        *,
        depth: int,
    ) -> Any:
        await self._maybe_yield(state)
        self._step(state, node)
        self._check_depth(depth, node)

        ntype = node.get("type")
        if ntype == NODE_LITERAL:
            value = node["value"]
            state.trace.append(
                {"nodeId": node.get("id"), "type": ntype, "value": value}
            )
            return value

        if ntype == NODE_FIELD:
            path = node["path"]
            if path not in ctx.resolved_fields:
                raise DslExecutionError(
                    detail=(
                        f"field.path '{path}' was not precomputed. This "
                        "usually means the validator was bypassed."
                    ),
                    headers={"X-Node-Id": str(node.get("id"))},
                    code="DSL_FIELD_NOT_PRECOMPUTED",
                    params={"nodeId": node.get("id"), "path": path},
                )
            value = ctx.resolved_fields[path]
            state.trace.append(
                {"nodeId": node.get("id"), "type": ntype, "value": value}
            )
            return value

        if ntype == NODE_ARITH:
            left = await self._eval_expression(
                node["left"], ctx, state, depth=depth + 1
            )
            right = await self._eval_expression(
                node["right"], ctx, state, depth=depth + 1
            )
            op = node["op"]
            if op not in ALLOWED_ARITH_OPS:
                raise DslValidationError(
                    detail=f"arith.op '{op}' is not allowed.",
                    headers={"X-Node-Id": str(node.get("id"))},
                    code="DSL_ARITH_OP_NOT_ALLOWED",
                    params={"nodeId": node.get("id"), "op": op},
                )
            try:
                result = _apply_arith(op, left, right)
            except ZeroDivisionError as exc:
                raise DslExecutionError(
                    detail="division by zero",
                    headers={"X-Node-Id": str(node.get("id"))},
                    code="DSL_ARITH_DIV_BY_ZERO",
                    params={"nodeId": node.get("id"), "op": op},
                ) from exc
            except TypeError as exc:
                raise DslExecutionError(
                    detail=(
                        f"arith {op!r} between incompatible types "
                        f"{type(left).__name__} and {type(right).__name__}."
                    ),
                    headers={"X-Node-Id": str(node.get("id"))},
                    code="DSL_ARITH_TYPE_MISMATCH",
                    params={
                        "nodeId": node.get("id"),
                        "op": op,
                        "leftType": type(left).__name__,
                        "rightType": type(right).__name__,
                    },
                ) from exc
            state.trace.append(
                {"nodeId": node.get("id"), "type": ntype, "value": result}
            )
            return result

        if ntype == NODE_FUNC_CALL:
            # Whitelist + arity are enforced by the validator before we
            # get here, but we re-check defensively so a bypassed AST
            # can't reach the handler table with an unknown name.
            name = node.get("name")
            if name not in ALLOWED_FUNC_NAMES:
                raise DslValidationError(
                    detail=f"func_call.name '{name}' is not allowed.",
                    headers={"X-Node-Id": str(node.get("id"))},
                    code="DSL_FUNC_NAME_NOT_ALLOWED",
                    params={"nodeId": node.get("id"), "name": name},
                )
            args_nodes = node.get("args") or []
            if len(args_nodes) != FUNC_ARITY[name]:
                raise DslValidationError(
                    detail=(
                        f"func_call '{name}' expects "
                        f"{FUNC_ARITY[name]} args, got {len(args_nodes)}."
                    ),
                    headers={"X-Node-Id": str(node.get("id"))},
                    code="DSL_FUNC_ARITY_MISMATCH",
                    params={
                        "nodeId": node.get("id"),
                        "name": name,
                        "expected": FUNC_ARITY[name],
                        "actual": len(args_nodes),
                    },
                )
            args = [
                await self._eval_expression(
                    arg, ctx, state, depth=depth + 1
                )
                for arg in args_nodes
            ]
            try:
                result = _apply_func(name, args)
            except (TypeError, ValueError, ZeroDivisionError) as exc:
                raise DslExecutionError(
                    detail=f"func_call '{name}' failed: {exc}",
                    headers={"X-Node-Id": str(node.get("id"))},
                ) from exc
            state.trace.append(
                {"nodeId": node.get("id"), "type": ntype, "value": result}
            )
            return result

        raise DslValidationError(
            detail=f"Unknown expression node type: '{ntype}'.",
            headers={"X-Node-Id": str(node.get("id"))},
        )

    # ----- guards ----------------------------------------------------------

    def _step(self, state: _RunState, node: Dict[str, Any]) -> None:
        state.count += 1
        if state.count > self._max_nodes:
            raise DslLimitExceededError(
                detail=(
                    f"DSL execution exceeded maximum node count "
                    f"({self._max_nodes})."
                ),
                headers={"X-Node-Id": str(node.get("id"))},
            )

    def _check_depth(self, depth: int, node: Dict[str, Any]) -> None:
        if depth > self._max_depth:
            raise DslLimitExceededError(
                detail=(
                    f"DSL execution exceeded maximum recursion depth "
                    f"({self._max_depth})."
                ),
                headers={"X-Node-Id": str(node.get("id"))},
            )

    async def _maybe_yield(self, state: _RunState) -> None:
        if state.count and state.count % self._yield_every == 0:
            await asyncio.sleep(0)


class _RunState:
    __slots__ = (
        "count",
        "trace",
        "points",
        "case_name",
        "callback_data",
        "matched",
        # Sprint 7: DSL_EXTEND state. ``working_data`` is the dict that
        # set_data writes to during pre_rules — the orchestrator reads
        # it back to hand to the parent built-in's calculate_points.
        # ``vetoed`` signals that a pre_rules veto fired so the
        # orchestrator skips parent + post entirely.
        "working_data",
        "vetoed",
    )

    def __init__(self) -> None:
        self.count: int = 0
        self.trace: List[Dict[str, Any]] = []
        self.points: float = 0
        self.case_name: Optional[str] = None
        self.callback_data: Dict[str, Any] = {}
        self.matched: bool = False
        self.working_data: Dict[str, Any] = {}
        self.vetoed: bool = False


_COMPARE_HANDLERS = {
    "<":  lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">=": lambda a, b: a >= b,
    ">":  lambda a, b: a > b,
}


def _apply_compare(op: str, left: Any, right: Any) -> bool:
    return bool(_COMPARE_HANDLERS[op](left, right))


_ARITH_HANDLERS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
    "min": lambda a, b: min(a, b),
    "max": lambda a, b: max(a, b),
}


def _apply_arith(op: str, left: Any, right: Any) -> Any:
    return _ARITH_HANDLERS[op](left, right)


# Sprint 6: handlers for the ``func_call`` node. Kept separate from the
# binary arith table because the arities and signatures differ. ``int``
# truncates toward zero (mirroring Python's built-in and matching
# ``constantEffortStrategy.py:53`` semantics — not rounding). ``clamp``
# is (value, lo, hi) → max(lo, min(value, hi)).
_FUNC_HANDLERS = {
    "int": lambda args: int(args[0]),
    "clamp": lambda args: max(args[1], min(args[0], args[2])),
}


def _apply_func(name: str, args: List[Any]) -> Any:
    return _FUNC_HANDLERS[name](args)
