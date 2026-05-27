"""
``BaseStrategy`` adapter that runs a persisted DSL ``StrategyDefinition``.

This class is built in Sprint 4 but NOT connected to ``UserPointsService``
yet — that wiring is Sprint 5's "modify BaseStrategy.calculate_points to
delegate" item. Until then the adapter is exercised only by the simulate
endpoint and by tests.

Notable choice: ``_generate_hash_of_calculate_points`` is overridden to
hash the canonicalized AST (sorted JSON keys) instead of the Python
source of the method. The built-in strategies still use the inspect-based
hash inherited from ``BaseStrategy``, so existing ``UserPoints``
idempotency keys remain valid — only DSL strategies opt into the new
hash scheme.
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
from typing import Any, Optional, Tuple

from app.core.config import configs
from app.core.exceptions import DslTimeoutError
from app.engine.base_strategy import BaseStrategy
from app.engine.dsl_execution_context import ExecutionContext
from app.engine.dsl_interpreter import DslInterpreter
from app.schema.strategy_definition_schema import StrategyDefinitionRead


class DslStrategy(BaseStrategy):
    def __init__(
        self,
        definition: StrategyDefinitionRead,
        interpreter: DslInterpreter,
        analytics_service: Any,
        *,
        parent_strategy: Optional[BaseStrategy] = None,
    ) -> None:
        # Skip the parent ``__init__`` because it eagerly computes the
        # hash from ``inspect.getsource(self.calculate_points)``, which
        # would hash THIS class's Python source — useless for DSL.
        self.debug = False
        self.strategy_name = definition.name
        self.strategy_description = definition.description
        self.strategy_name_slug = definition.name
        self.strategy_version = str(definition.version)
        self.variable_basic_points = 1
        self.variable_bonus_points = 1
        self._definition = definition
        self._interpreter = interpreter
        self._analytics = analytics_service
        # Sprint 7: when set, calculate_points runs the DSL_EXTEND
        # pipeline (pre_rules → parent.calculate_points → post_rules).
        # Injected by StrategyService.get_strategy_instance only when
        # the definition is DSL_EXTEND.
        self._parent_strategy = parent_strategy
        self.hash_version = self._generate_hash_of_calculate_points()

    def _generate_hash_of_calculate_points(self) -> str:
        payload = self._definition.astJson or {}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get_strategy_id(self) -> str:
        return f"custom:{self._definition.id}"

    async def calculate_points(
        self,
        externalGameId: Optional[str] = None,
        externalTaskId: Optional[str] = None,
        externalUserId: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> Tuple:
        if self._definition.astJson is None:
            return 0, None

        if self._parent_strategy is None:
            return await self._calculate_dsl_full(
                externalGameId, externalTaskId, externalUserId, data,
            )
        return await self._calculate_dsl_extend(
            externalGameId, externalTaskId, externalUserId, data,
        )

    # ----- DSL_FULL (Sprint 5) ----------------------------------------------

    async def _calculate_dsl_full(
        self,
        externalGameId: Optional[str],
        externalTaskId: Optional[str],
        externalUserId: Optional[str],
        data: Optional[dict],
    ) -> Tuple:
        ctx = await ExecutionContext.build_for_ast(
            self._definition.astJson,
            externalGameId=externalGameId,
            externalTaskId=externalTaskId,
            externalUserId=externalUserId,
            data=data,
            analytics_service=self._analytics,
        )
        result = await self._run_phase(
            ctx, mode="full",
            initial_data=None, parent_result=None,
        )
        return self._format_result(result)

    # ----- DSL_EXTEND (Sprint 7) --------------------------------------------

    async def _calculate_dsl_extend(
        self,
        externalGameId: Optional[str],
        externalTaskId: Optional[str],
        externalUserId: Optional[str],
        data: Optional[dict],
    ) -> Tuple:
        """
        3-phase pipeline:
          1. ``pre_rules`` may mutate ``data`` (set_data) or veto.
          2. The parent built-in's ``calculate_points`` runs against
             the (possibly mutated) data with parent_variables applied.
          3. ``post_rules`` mutates the parent's result via set_points
             / set_case_name / set_callback_data and may read
             parent.points / parent.case_name as field paths.

        Each phase gets its own ExecutionContext (the second one carries
        parent_result so the post-rules see parent.* values). This keeps
        the frozen-context invariant intact instead of mutating one
        context in place across phases.
        """
        ast = self._definition.astJson
        ast_pre = ast.get("pre_rules") or []
        ast_post = ast.get("post_rules") or []
        parent_variable_overrides = ast.get("parent_variables") or {}

        # Phase 1 — pre_rules. We build a context that doesn't carry
        # parent.* fields (those paths are validator-rejected outside
        # post_rules anyway). The interpreter copies ``data`` into
        # state.working_data so set_data mutations are local to this
        # request.
        working_data: dict = dict(data or {})
        if ast_pre:
            pre_ctx = await ExecutionContext.build_for_ast(
                ast,
                externalGameId=externalGameId,
                externalTaskId=externalTaskId,
                externalUserId=externalUserId,
                data=working_data,
                analytics_service=self._analytics,
            )
            pre_result = await self._run_phase(
                pre_ctx, mode="pre",
                initial_data=working_data, parent_result=None,
            )
            if pre_result.get("vetoed"):
                # Pre-rule veto short-circuits the whole pipeline: parent
                # never runs, post_rules never run. The veto's case_name
                # and any callback_data accumulated before it are the
                # final result.
                return self._format_result(pre_result)
            working_data = pre_result["working_data"]

        # Phase 2 — parent built-in. We only shallow-copy when there
        # are variable overrides; otherwise we reuse the registry
        # singleton directly. This matters because (a) skipping the
        # copy when unnecessary avoids paying for ``__dict__``
        # duplication on every request, and (b) tests that introspect
        # the original instance (e.g. ``parent.last_call_args``) only
        # see the call when the orchestrator targets the original.
        # When overrides exist we DO need the copy so the next request
        # — or another DSL_EXTEND row that shares the same parent —
        # doesn't inherit this realm's tweaked variables.
        parent_instance = self._parent_strategy
        if parent_variable_overrides:
            parent_instance = copy.copy(parent_instance)
            parent_instance.set_variables(parent_variable_overrides)
        parent_tuple = await parent_instance.calculate_points(
            externalGameId=externalGameId,
            externalTaskId=externalTaskId,
            externalUserId=externalUserId,
            data=working_data,
        )
        parent_result = _normalize_parent_tuple(parent_tuple)

        # Phase 3 — post_rules. The state is bootstrapped from
        # parent_result so set_points / set_case_name mutate from the
        # parent's output as the starting point. The new ExecutionContext
        # carries parent.* fields so post-rule conditions can branch on
        # the parent's caseName ("if parent emitted PerformanceBonus,
        # multiply by 1.5"…).
        if not ast_post:
            return self._format_result({
                "points": parent_result["points"],
                "case_name": parent_result["case_name"],
                "callback_data": parent_result["callback_data"],
                "trace": [],
            })

        post_ctx = await ExecutionContext.build_for_ast(
            ast,
            externalGameId=externalGameId,
            externalTaskId=externalTaskId,
            externalUserId=externalUserId,
            data=working_data,
            analytics_service=self._analytics,
            parent_result=parent_result,
        )
        post_result = await self._run_phase(
            post_ctx, mode="post",
            initial_data=None, parent_result=parent_result,
        )
        return self._format_result(post_result)

    # ----- shared helpers ---------------------------------------------------

    async def _run_phase(
        self,
        ctx: ExecutionContext,
        *,
        mode: str,
        initial_data: Optional[dict],
        parent_result: Optional[dict],
    ) -> dict:
        """Run one phase under the per-call timeout and return the raw
        DslExecutionResult dict (which carries working_data and vetoed
        for pre/post phases — see the TypedDict in dsl_interpreter)."""
        try:
            return await asyncio.wait_for(
                self._interpreter.execute(
                    self._definition.astJson, ctx,
                    mode=mode,
                    initial_data=initial_data,
                    parent_result=parent_result,
                ),
                timeout=configs.DSL_EXECUTION_TIMEOUT_MS / 1000,
            )
        except asyncio.TimeoutError as exc:
            raise DslTimeoutError(
                detail=(
                    "DSL strategy execution exceeded the "
                    f"{configs.DSL_EXECUTION_TIMEOUT_MS}ms time limit."
                )
            ) from exc

    def _format_result(self, run: dict) -> Tuple:
        cb = run.get("callback_data") or {}
        if cb:
            return run["points"], run.get("case_name"), cb
        return run["points"], run.get("case_name")


def _normalize_parent_tuple(parent_tuple: Any) -> dict:
    """The built-in calculate_points may return 2 or 3 elements (see
    user_points_service.py line 636's ``(... + (None,))[:3]`` pattern).
    Normalise to a uniform dict the rest of the orchestrator can rely
    on."""
    if not isinstance(parent_tuple, tuple):
        return {"points": 0, "case_name": None, "callback_data": {}}
    padded = parent_tuple + (None,)
    points, case_name, callback_data = padded[:3]
    return {
        "points": points if points is not None else 0,
        "case_name": case_name,
        "callback_data": dict(callback_data) if callback_data else {},
    }
