"""
Service that dry-runs a persisted DSL strategy without touching points,
wallets, or user state.

Used by the ``POST /v1/strategies/custom/{id}/simulate`` endpoint so a
designer can iterate on rule logic before publishing. The service is the
only place that combines the strategy definition (loaded via
:class:`StrategyDefinitionService`, which enforces realm scoping), the
precompute pipeline, and the timeout-wrapped interpreter run. Everything
else is plain data shuffling.

Mocks: when ``request.mockState`` is provided, the analytics service is
not called for the mocked paths. This makes simulations deterministic
and lets designers see the consequences of "what if the user had X
measurements?" without manipulating production data.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.config import configs
from app.core.exceptions import DslTimeoutError, DslValidationError
from app.engine.dsl_execution_context import ExecutionContext
from app.engine.dsl_interpreter import DslInterpreter
from app.engine.dsl_validator import validate_ast
from app.schema.dsl_schema import (ExecutionTraceEntry, InlineSimulationRequest,
                                   SimulationRequest, SimulationResponse)
from app.services.base_service import BaseService
from app.services.strategy_definition_service import StrategyDefinitionService
from app.services.user_points_analytics_service import UserPointsAnalyticsService


class DslSimulationService(BaseService):
    def __init__(
        self,
        strategy_definition_service: StrategyDefinitionService,
        user_points_analytics_service: UserPointsAnalyticsService,
    ) -> None:
        self.strategy_definition_service = strategy_definition_service
        self.user_points_analytics_service = user_points_analytics_service
        super().__init__(strategy_definition_service)

    async def simulate(
        self,
        *,
        id: str,
        realmId: Any,
        request: SimulationRequest,
    ) -> SimulationResponse:
        definition = await self.strategy_definition_service.get_strategy(
            id=id, realmId=realmId
        )

        if not definition.astJson:
            raise DslValidationError(
                detail=(
                    "Strategy has no AST to simulate. Provide an astJson "
                    "via PUT /v1/strategies/custom/{id} first."
                ),
                code="DSL_NO_AST_TO_SIMULATE",
                params={"strategyId": id},
            )

        return await self._run_ast(definition.astJson, request)

    async def simulate_inline(
        self,
        *,
        realmId: Any,
        request: InlineSimulationRequest,
    ) -> SimulationResponse:
        """Sprint 5 (fix C7): dry-run an AST supplied inline.

        No DB lookup and nothing persisted, so "Probar" no longer spawns
        orphan DRAFT rows and tests the exact AST on the editor canvas
        (including unsaved edits). ``realmId`` is accepted for symmetry
        with :meth:`simulate` and to keep the door open for per-tenant
        analytics scoping; the sandbox run itself is bounded by the same
        node/depth/timeout limits regardless of tenant.
        """
        return await self._run_ast(request.astJson, request)

    async def _run_ast(
        self,
        astJson: Any,
        request: SimulationRequest,
    ) -> SimulationResponse:
        """Validate ``astJson`` and run it through the timeout-wrapped
        interpreter, returning the structured simulation response. Shared
        by the id-based and inline simulate paths so both stay in lockstep.
        """
        # Idempotent guard: drafts saved before validator changes still
        # need to fail loudly rather than half-run.
        validate_ast(astJson)

        ctx = await ExecutionContext.build_for_ast(
            astJson,
            externalGameId=request.externalGameId,
            externalTaskId=request.externalTaskId,
            externalUserId=request.externalUserId,
            data=request.data,
            analytics_service=self.user_points_analytics_service,
            mock_state=request.mockState,
        )

        interpreter = DslInterpreter(
            max_nodes=configs.DSL_MAX_NODES,
            max_depth=configs.DSL_MAX_DEPTH,
        )

        try:
            result = await asyncio.wait_for(
                interpreter.execute(astJson, ctx),
                timeout=configs.DSL_EXECUTION_TIMEOUT_MS / 1000,
            )
        except asyncio.TimeoutError as exc:
            raise DslTimeoutError(
                detail=(
                    f"DSL simulation exceeded the "
                    f"{configs.DSL_EXECUTION_TIMEOUT_MS}ms time limit."
                ),
                code="DSL_TIMEOUT",
                params={"timeoutMs": configs.DSL_EXECUTION_TIMEOUT_MS},
            ) from exc

        return SimulationResponse(
            points=float(result["points"]),
            caseName=result["case_name"],
            callbackData=dict(result["callback_data"]),
            executionTrace=[ExecutionTraceEntry(**entry) for entry in result["trace"]],
        )
