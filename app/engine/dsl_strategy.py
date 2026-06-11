"""
``BaseStrategy`` adapter that runs a persisted DSL ``StrategyDefinition``.

This adapter is what ``StrategyService`` instantiates for ``custom:`` ids;
it is also exercised directly by the simulate endpoint and by tests.

Notable choice: ``_generate_hash_of_calculate_points`` is overridden to
hash the canonicalized AST (sorted JSON keys) instead of the Python
source of the method. The built-in strategies still use the inspect-based
hash inherited from ``BaseStrategy``, so existing ``UserPoints``
idempotency keys remain valid - only DSL strategies opt into the new
hash scheme.
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import time
from collections import OrderedDict
from typing import Any, Optional, Tuple

from app.core.config import configs
from app.core.exceptions import (DslExecutionError, DslLimitExceededError,
                                 DslTimeoutError, DslValidationError)
from app.engine.base_strategy import BaseStrategy
from app.engine.dsl_execution_context import ExecutionContext
from app.engine.dsl_interpreter import DslInterpreter
from app.schema.strategy_definition_schema import StrategyDefinitionRead

# The idempotency hash is a canonical-JSON dump of the AST
# plus a SHA-256 - pure CPU, but ``UserPointsService`` constructs a fresh
# ``DslStrategy`` on every scoring call, so a busy strategy re-hashes the
# same multi-KB AST thousands of times a minute. We memoise the result
# keyed by ``(strategyId, version)``.
#
# Only PUBLISHED definitions are cached: editing a DRAFT patches the row
# *in place* without bumping the version (see
# ``StrategyDefinitionService.update_strategy``), so ``(id, version)`` is
# not a stable key for drafts. PUBLISHED rows are immutable - an edit
# forks a new version - so the key is 1:1 with the AST, and scoring only
# ever runs published strategies anyway. The simulate path (drafts)
# recomputes, which is fine: it isn't the hot path.
#
# The cache is a small bounded LRU; cardinality is (published strategies ×
# versions) for the realms hot in this process.
_PUBLISHED_HASH_CACHE: "OrderedDict[Tuple[str, int], str]" = OrderedDict()
_PUBLISHED_HASH_CACHE_MAXSIZE = 512


def _compute_ast_hash(ast: Optional[dict]) -> str:
    """
    Return a stable sha256 hex digest of a DSL AST.

    The AST is serialized with sorted keys and compact separators so logically
    equivalent ASTs always hash identically.

    Args:
        ast (Optional[dict]): The strategy AST (``None`` is treated as ``{}``).

    Returns:
        str: The hex-encoded sha256 digest.
    """
    canonical = json.dumps(ast or {}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _cached_published_ast_hash(
    strategy_id: str, version: int, ast: Optional[dict]
) -> str:
    """
    Return the AST hash for a published strategy, memoized in a process LRU.

    Published ``(strategy_id, version)`` pairs are immutable, so their hash is
    cached to avoid re-hashing on every scoring call; the LRU is bounded by
    ``_PUBLISHED_HASH_CACHE_MAXSIZE``.

    Args:
        strategy_id (str): The strategy definition id.
        version (int): The published version number.
        ast (Optional[dict]): The strategy AST to hash on a cache miss.

    Returns:
        str: The hex-encoded sha256 digest.
    """
    key = (strategy_id, version)
    cached = _PUBLISHED_HASH_CACHE.get(key)
    if cached is not None:
        _PUBLISHED_HASH_CACHE.move_to_end(key)
        return cached
    value = _compute_ast_hash(ast)
    _PUBLISHED_HASH_CACHE[key] = value
    if len(_PUBLISHED_HASH_CACHE) > _PUBLISHED_HASH_CACHE_MAXSIZE:
        _PUBLISHED_HASH_CACHE.popitem(last=False)
    return value


class DslStrategy(BaseStrategy):
    def __init__(
        self,
        definition: StrategyDefinitionRead,
        interpreter: DslInterpreter,
        analytics_service: Any,
        *,
        parent_strategy: Optional[BaseStrategy] = None,
        observer: Optional[Any] = None,
    ) -> None:
        # Skip the parent ``__init__`` because it eagerly computes the
        # hash from ``inspect.getsource(self.calculate_points)``, which
        # would hash THIS class's Python source - useless for DSL.
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
        # When set, calculate_points runs the DSL_EXTEND
        # pipeline (pre_rules → parent.calculate_points → post_rules).
        # Injected by StrategyService.get_strategy_instance only when
        # the definition is DSL_EXTEND.
        self._parent_strategy = parent_strategy
        # Observer sink for metrics + sampled persistence.
        # Optional so unit tests instantiating DslStrategy without the
        # container keep working unchanged. The container wires the
        # real DslExecutionObserver in production.
        self._observer = observer
        # Filled by _run_phase on every interpreter call so
        # the calculate_points wrapper can hand the observer a trace
        # without threading return values through DSL_EXTEND's three
        # phases. Reset at the top of every calculate_points entry.
        self._last_trace: Optional[list] = None
        self._last_nodes_executed: int = 0
        self.hash_version = self._generate_hash_of_calculate_points()

    def _generate_hash_of_calculate_points(self) -> str:
        """
        Compute the version hash identifying this strategy's scoring logic.

        Published definitions reuse the process-wide LRU
        (:func:`_cached_published_ast_hash`); drafts, whose ``(id, version)``
        is not stable, are hashed fresh each time.

        Returns:
            str: The AST-derived hash stored as ``hash_version``.
        """
        # Published definitions hit the process-wide LRU so the
        # same AST isn't re-hashed on every scoring call; drafts (whose
        # (id, version) key is not stable) always recompute.
        if getattr(self._definition, "status", None) == "PUBLISHED":
            return _cached_published_ast_hash(
                str(self._definition.id),
                self._definition.version,
                self._definition.astJson,
            )
        return _compute_ast_hash(self._definition.astJson)

    def get_strategy_id(self) -> str:
        """
        Return the public id for this custom strategy.

        Returns:
            str: The id in the form ``"custom:<definition id>"``.
        """
        return f"custom:{self._definition.id}"

    async def calculate_points(
        self,
        externalGameId: Optional[str] = None,
        externalTaskId: Optional[str] = None,
        externalUserId: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> Tuple:
        """
        Score an event by running this custom strategy's DSL program.

        Dispatches to the DSL_FULL pipeline, or the DSL_EXTEND pipeline
        (pre-rules → parent strategy → post-rules) when a parent strategy is
        configured. Every call is wrapped in a single observability envelope
        that records timing, status, node count and trace for metrics and
        sampled persistence, regardless of success or failure.

        Args:
            externalGameId (Optional[str]): External identifier of the game.
            externalTaskId (Optional[str]): External identifier of the task.
            externalUserId (Optional[str]): External identifier of the user.
            data (Optional[dict]): Event payload available to the program.

        Returns:
            tuple: ``(points, case_name)`` or ``(points, case_name,
            callback_data)`` produced by the program; ``(0, None)`` when the
            definition has no AST.
        """
        if self._definition.astJson is None:
            return 0, None

        # Reset per-call observability state so a previous run's trace
        # (e.g. from a re-used strategy instance) doesn't leak into
        # this one's observer payload.
        self._last_trace = None
        self._last_nodes_executed = 0

        # Every execution gets a single observation envelope
        # so metrics + sampled persistence cover both DSL_FULL and
        # DSL_EXTEND (and both success and failure) on one code path.
        # The envelope is intentionally outside _calculate_dsl_* so it
        # captures precompute + interpreter time both.
        start = time.perf_counter()
        status = "ok"
        error_code: Optional[str] = None
        trace: Optional[list] = None
        nodes_executed = 0
        points_emitted: Optional[float] = None
        case_name_emitted: Optional[str] = None
        try:
            if self._parent_strategy is None:
                result = await self._calculate_dsl_full(
                    externalGameId,
                    externalTaskId,
                    externalUserId,
                    data,
                )
            else:
                result = await self._calculate_dsl_extend(
                    externalGameId,
                    externalTaskId,
                    externalUserId,
                    data,
                )
            # ``result`` is the 2- or 3-tuple
            # (points, case_name [, callback_data]). Normalise for the
            # observer; the caller still gets the original tuple back.
            padded = result + (None,)
            points_emitted, case_name_emitted, _cb = padded[:3]
            # Pull the last-run trace / node count off the strategy so
            # we don't have to thread them through every return path.
            trace = self._last_trace
            nodes_executed = self._last_nodes_executed
            return result
        except DslTimeoutError as exc:
            status = "timeout"
            error_code = getattr(exc, "code", None) or "DSL_TIMEOUT"
            raise
        except DslLimitExceededError as exc:
            status = "limit"
            error_code = getattr(exc, "code", None) or "DSL_LIMIT_EXCEEDED"
            raise
        except (DslExecutionError, DslValidationError) as exc:
            status = "error"
            error_code = getattr(exc, "code", None) or exc.__class__.__name__
            raise
        except Exception:
            status = "error"
            error_code = "DSL_UNEXPECTED"
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            if self._observer is not None:
                # The observer never raises -- it logs internally if
                # the metrics or insert blow up. Awaiting it here is
                # safe because the only awaitable inside is a fast
                # repository write.
                try:
                    await self._observer.record(
                        strategyId=str(self._definition.id),
                        strategyVersion=self._definition.version,
                        strategyType=self._definition.type,
                        realmId=self._definition.realmId,
                        externalGameId=externalGameId,
                        externalTaskId=externalTaskId,
                        externalUserId=externalUserId,
                        status=status,
                        errorCode=error_code,
                        points=(
                            float(points_emitted)
                            if isinstance(points_emitted, (int, float))
                            and not isinstance(points_emitted, bool)
                            else None
                        ),
                        caseName=case_name_emitted,
                        durationMs=duration_ms,
                        nodesExecuted=nodes_executed,
                        trace=trace,
                        parentStrategyId=(self._definition.parentStrategyId),
                    )
                except Exception:  # pragma: no cover - defensive
                    # Never let observability bubble up. The observer
                    # already logs; swallowing here protects the
                    # scoring path from a broken sink.
                    pass

    async def _calculate_dsl_full(
        self,
        externalGameId: Optional[str],
        externalTaskId: Optional[str],
        externalUserId: Optional[str],
        data: Optional[dict],
    ) -> Tuple:
        """
        Run the DSL_FULL pipeline: build a context and execute the program.

        Constructs an :class:`ExecutionContext` (precomputing the whitelisted
        fields the AST references) and runs the program's single phase.

        Args:
            externalGameId (Optional[str]): External identifier of the game.
            externalTaskId (Optional[str]): External identifier of the task.
            externalUserId (Optional[str]): External identifier of the user.
            data (Optional[dict]): Event payload available to the program.

        Returns:
            tuple: The ``(points, case_name[, callback_data])`` result.
        """
        ctx = await ExecutionContext.build_for_ast(
            self._definition.astJson,
            externalGameId=externalGameId,
            externalTaskId=externalTaskId,
            externalUserId=externalUserId,
            data=data,
            analytics_service=self._analytics,
        )
        result = await self._run_phase(
            ctx,
            mode="full",
            initial_data=None,
            parent_result=None,
        )
        return self._format_result(result)

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

        # DSL_EXTEND builds up to two ExecutionContexts (pre +
        # post) for the same user and request window. Share one analytics
        # memo across both so each analytics field (a DB round-trip)
        # resolves once instead of twice. Static and data.* fields are not
        # cached (cheap / phase-dependent), so this is safe even though
        # pre-rules mutate ``data`` between the two builds.
        analytics_cache: dict = {}

        # Phase 1 - pre_rules. We build a context that doesn't carry
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
                analytics_cache=analytics_cache,
            )
            pre_result = await self._run_phase(
                pre_ctx,
                mode="pre",
                initial_data=working_data,
                parent_result=None,
            )
            if pre_result.get("vetoed"):
                # Pre-rule veto short-circuits the whole pipeline: parent
                # never runs, post_rules never run. The veto's case_name
                # and any callback_data accumulated before it are the
                # final result.
                return self._format_result(pre_result)
            working_data = pre_result["working_data"]

        # Phase 2 - parent built-in. We only shallow-copy when there
        # are variable overrides; otherwise we reuse the registry
        # singleton directly. This matters because (a) skipping the
        # copy when unnecessary avoids paying for ``__dict__``
        # duplication on every request, and (b) tests that introspect
        # the original instance (e.g. ``parent.last_call_args``) only
        # see the call when the orchestrator targets the original.
        # When overrides exist we DO need the copy so the next request
        # - or another DSL_EXTEND row that shares the same parent -
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

        # Phase 3 - post_rules. The state is bootstrapped from
        # parent_result so set_points / set_case_name mutate from the
        # parent's output as the starting point. The new ExecutionContext
        # carries parent.* fields so post-rule conditions can branch on
        # the parent's caseName ("if parent emitted PerformanceBonus,
        # multiply by 1.5"…).
        if not ast_post:
            return self._format_result(
                {
                    "points": parent_result["points"],
                    "case_name": parent_result["case_name"],
                    "callback_data": parent_result["callback_data"],
                    "trace": [],
                }
            )

        post_ctx = await ExecutionContext.build_for_ast(
            ast,
            externalGameId=externalGameId,
            externalTaskId=externalTaskId,
            externalUserId=externalUserId,
            data=working_data,
            analytics_service=self._analytics,
            parent_result=parent_result,
            analytics_cache=analytics_cache,
        )
        post_result = await self._run_phase(
            post_ctx,
            mode="post",
            initial_data=None,
            parent_result=parent_result,
        )
        return self._format_result(post_result)

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
        for pre/post phases - see the TypedDict in dsl_interpreter).

        The trace produced by each phase is appended to
        ``self._last_trace`` so the calculate_points wrapper hands the
        observer a single sequential trace for the whole pipeline (pre
        + post for DSL_EXTEND, just the full run for DSL_FULL). Node
        counts are summed for the same reason.
        """
        try:
            result = await asyncio.wait_for(
                self._interpreter.execute(
                    self._definition.astJson,
                    ctx,
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

        phase_trace = result.get("trace") or []
        if self._last_trace is None:
            self._last_trace = list(phase_trace)
        else:
            self._last_trace.extend(phase_trace)
        self._last_nodes_executed += len(phase_trace)
        return dict(result)

    def _format_result(self, run: dict) -> Tuple:
        """
        Convert an internal run dict into the public result tuple.

        Args:
            run (dict): Run result with ``points``, ``case_name`` and optional
                ``callback_data``.

        Returns:
            tuple: ``(points, case_name, callback_data)`` when callback data is
            present, otherwise ``(points, case_name)``.
        """
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
