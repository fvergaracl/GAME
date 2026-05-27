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
        ctx = await ExecutionContext.build_for_ast(
            self._definition.astJson,
            externalGameId=externalGameId,
            externalTaskId=externalTaskId,
            externalUserId=externalUserId,
            data=data,
            analytics_service=self._analytics,
        )
        try:
            result = await asyncio.wait_for(
                self._interpreter.execute(self._definition.astJson, ctx),
                timeout=configs.DSL_EXECUTION_TIMEOUT_MS / 1000,
            )
        except asyncio.TimeoutError as exc:
            raise DslTimeoutError(
                detail=(
                    "DSL strategy execution exceeded the "
                    f"{configs.DSL_EXECUTION_TIMEOUT_MS}ms time limit."
                )
            ) from exc
        if result["callback_data"]:
            return result["points"], result["case_name"], result["callback_data"]
        return result["points"], result["case_name"]
