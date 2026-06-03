"""
ExecutionContext: precomputes everything a strategy AST will need so the
interpreter walk is pure CPU and never makes a database call.

The precompute strategy is deliberately lazy at the AST level: we walk
the tree once, collect the set of ``field`` paths it actually reads, and
only fetch (or mock) those. A strategy that ignores ``user.avg_time``
pays no cost for it. A malicious AST that tries to reference an unknown
path is rejected by the validator long before we get here.

``mock_state`` is the back door used by the ``/simulate`` endpoint: keys
are dotted-path strings matching ``FIELD_RESOLVERS`` entries (or ``data.*``
prefixes). When present, the precompute uses the mock value verbatim and
never calls the analytics service. This is what lets a designer iterate
on logic against synthetic inputs while still hitting real production
analytics methods when ``mock_state`` is left unset.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Set

from app.engine.dsl_ast import (DATA_FIELD_PREFIX, FIELD_RESOLVERS, PARENT_FIELD_PATHS,
                                enumerate_field_paths, is_parent_field_path,
                                is_valid_data_path)


@dataclass(frozen=True)
class ExecutionContext:
    externalGameId: str
    externalTaskId: str
    externalUserId: str
    data: Mapping[str, Any]
    resolved_fields: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    async def build_for_ast(
        cls,
        ast: Dict[str, Any],
        *,
        externalGameId: str,
        externalTaskId: str,
        externalUserId: str,
        data: Optional[Dict[str, Any]],
        analytics_service: Any,
        mock_state: Optional[Dict[str, Any]] = None,
        parent_result: Optional[Dict[str, Any]] = None,
        analytics_cache: Optional[Dict[str, Any]] = None,
    ) -> "ExecutionContext":
        """
        Precompute every field referenced by ``ast`` and return a frozen
        context the interpreter can walk synchronously.

        The static paths are computed without any I/O. Analytics paths
        each trigger at most one awaited call to the analytics service,
        and only when the AST actually references them. ``mock_state``
        short-circuits both, useful for the simulate endpoint and for
        tests that don't want a real DB.

        Sprint 13 — ``analytics_cache`` is an optional caller-owned dict
        memoising analytics-field values *within a single scoring call*.
        DSL_EXTEND builds two contexts (pre + post) for the same user and
        request window; passing the same dict to both means each analytics
        method (a DB round-trip) runs once instead of twice. Only
        ``analytics``-kind fields are cached: static fields are pure CPU,
        and ``data.*`` fields legitimately differ between phases because
        pre-rules may mutate ``data``. Pass ``None`` (the default) to opt
        out — DSL_FULL builds a single context and gains nothing.
        """
        data_payload: Dict[str, Any] = dict(data or {})
        mocks = mock_state or {}

        # We materialise a NamedSpace-style minimal object for the
        # FieldResolution lambdas; building a tiny dataclass instance
        # would create a second source of truth for the same three
        # fields. A SimpleNamespace is the smallest thing that works.
        ctx_for_args = _IdsOnly(
            externalGameId=externalGameId,
            externalTaskId=externalTaskId,
            externalUserId=externalUserId,
        )

        referenced: Set[str] = enumerate_field_paths(ast)
        resolved: Dict[str, Any] = {}

        for path in referenced:
            if path in mocks:
                resolved[path] = mocks[path]
                continue
            if path in FIELD_RESOLVERS:
                resolution = FIELD_RESOLVERS[path]
                if resolution.kind == "static":
                    resolved[path] = resolution.arg_fn(ctx_for_args)
                    continue
                if resolution.kind == "analytics":
                    if analytics_cache is not None and path in analytics_cache:
                        resolved[path] = analytics_cache[path]
                        continue
                    method = getattr(analytics_service, resolution.method)
                    args = resolution.arg_fn(ctx_for_args)
                    value = await method(*args)
                    resolved[path] = value
                    if analytics_cache is not None:
                        analytics_cache[path] = value
                    continue
            if is_valid_data_path(path):
                key = path[len(DATA_FIELD_PREFIX) :]
                resolved[path] = data_payload.get(key)
                continue
            if is_parent_field_path(path):
                # Sprint 7: parent.* fields land here only when the
                # caller provided ``parent_result`` (DSL_EXTEND post
                # phase). Outside of that the validator should have
                # rejected the AST already (parent.* paths are only
                # valid inside post_rules). If parent_result is missing
                # we leave the slot unset so the interpreter surfaces a
                # clean error.
                continue
            # Validator should have caught this — if it didn't, leave the
            # field unresolved and let the interpreter surface a clean
            # error rather than silently returning None.

        # Sprint 7: inject parent.* AFTER the regular resolution loop so
        # post-rule execution can read the parent built-in's output via
        # the same ``ctx.resolved_fields`` lookup used for analytics.
        # Mock state still wins (mocks were already applied above) —
        # this only fills in slots the simulation didn't override.
        if parent_result is not None:
            for parent_path in PARENT_FIELD_PATHS:
                if parent_path in mocks:
                    continue
                # parent.<attr> → result["<attr>"] (case_name, points).
                attr = parent_path.split(".", 1)[1]
                resolved[parent_path] = parent_result.get(attr)

        return cls(
            externalGameId=externalGameId,
            externalTaskId=externalTaskId,
            externalUserId=externalUserId,
            data=MappingProxyType(data_payload),
            resolved_fields=MappingProxyType(resolved),
        )


@dataclass(frozen=True)
class _IdsOnly:
    """Minimal record passed to ``FieldResolution.arg_fn`` builders."""

    externalGameId: str
    externalTaskId: str
    externalUserId: str
