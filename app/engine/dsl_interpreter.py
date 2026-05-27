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
    NODE_AND,
    NODE_ARITH,
    NODE_ASSIGN_POINTS,
    NODE_COMPARE,
    NODE_FIELD,
    NODE_LITERAL,
    NODE_NOT,
    NODE_OR,
    NODE_RETURN,
    NODE_SET_CALLBACK_DATA,
)
from app.engine.dsl_execution_context import ExecutionContext


class DslExecutionResult(TypedDict):
    points: float
    case_name: Optional[str]
    callback_data: Dict[str, Any]
    trace: List[Dict[str, Any]]


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
        self, ast: Dict[str, Any], ctx: ExecutionContext
    ) -> DslExecutionResult:
        """Walk ``ast`` to completion and return the result."""
        state = _RunState()
        try:
            await self._run_program(ast, ctx, state)
        except _DslHalt:
            pass

        return {
            "points": state.points if state.matched else 0,
            "case_name": state.case_name,
            "callback_data": state.callback_data,
            "trace": state.trace,
        }

    # ----- top-level dispatch ----------------------------------------------

    async def _run_program(
        self, node: Dict[str, Any], ctx: ExecutionContext, state: _RunState
    ) -> None:
        self._step(state, node)
        for rule in node.get("rules") or []:
            await self._run_rule(rule, ctx, state, depth=1)

        default = node.get("default")
        if default is not None and not state.matched:
            await self._run_statement(default, ctx, state, depth=1)

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
        matched = await self._eval_condition(
            node["when"], ctx, state, depth=depth + 1
        )
        state.trace.append(
            {
                "nodeId": node.get("id"),
                "type": "rule",
                "value": bool(matched),
                "branch": "match" if matched else "skip",
            }
        )
        if not matched:
            return
        for stmt in node.get("then") or []:
            await self._run_statement(stmt, ctx, state, depth=depth + 1)

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
                )
            try:
                result = _apply_arith(op, left, right)
            except ZeroDivisionError as exc:
                raise DslExecutionError(
                    detail="division by zero",
                    headers={"X-Node-Id": str(node.get("id"))},
                ) from exc
            except TypeError as exc:
                raise DslExecutionError(
                    detail=(
                        f"arith {op!r} between incompatible types "
                        f"{type(left).__name__} and {type(right).__name__}."
                    ),
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
    )

    def __init__(self) -> None:
        self.count: int = 0
        self.trace: List[Dict[str, Any]] = []
        self.points: float = 0
        self.case_name: Optional[str] = None
        self.callback_data: Dict[str, Any] = {}
        self.matched: bool = False


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
}


def _apply_arith(op: str, left: Any, right: Any) -> Any:
    return _ARITH_HANDLERS[op](left, right)
