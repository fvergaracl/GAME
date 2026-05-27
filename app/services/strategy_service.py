from typing import Any, Optional

from app.core.exceptions import NotFoundError
from app.engine.all_engine_strategies import all_engine_strategies
from app.services.base_service import BaseService
from app.services.strategy_definition_service import (
    StrategyDefinitionService,
)

# Prefix used to address DB-persisted custom strategies from the existing
# ``Games.strategyId`` / ``Tasks.strategyId`` columns. Anything without this
# prefix is resolved against the in-process registry, preserving the
# pre-Sprint-3 behaviour. See the Sprint 3 compat-layer notes in the
# roadmap.
CUSTOM_STRATEGY_PREFIX = "custom:"


def is_custom_strategy_id(strategy_id: Optional[str]) -> bool:
    """Return True when ``strategy_id`` addresses a DB-stored strategy."""
    return bool(strategy_id) and strategy_id.startswith(CUSTOM_STRATEGY_PREFIX)


def parse_custom_strategy_id(strategy_id: str) -> str:
    """Strip the ``custom:`` prefix and return the underlying uuid."""
    return strategy_id[len(CUSTOM_STRATEGY_PREFIX):]


class StrategyService(BaseService):
    """
    Service class for managing strategies.

    Resolution is a two-step routing:
      * built-in strategies (registry-discovered ``BaseStrategy``
        subclasses) keep their bare id, e.g. ``"default"``.
      * persistent strategies authored from the dashboard live in the
        ``strategydefinition`` table and are addressed as
        ``"custom:<uuid>"``. The resolver returns a thin descriptor for
        them; the DSL interpreter that actually runs the AST lands in
        Sprint 4 and will plug into this same method.
    """

    def __init__(
        self,
        strategy_definition_service: Optional[
            StrategyDefinitionService
        ] = None,
    ) -> None:
        """
        Initializes the StrategyService.

        ``strategy_definition_service`` is optional so legacy call sites
        that only need built-ins still work after the Sprint 3 wiring.
        When it's omitted, attempting to resolve a ``custom:`` id raises
        ``NotFoundError`` with a clear message rather than silently
        crashing.
        """
        super().__init__(None)
        self._strategy_definition_service = strategy_definition_service

    def list_all_strategies(self) -> list[dict[str, Any]]:
        """
        Lists all available built-in strategies.

        Custom DB-stored strategies are returned through the dedicated
        ``/v1/strategies/custom`` endpoints rather than mixed in here, so
        the legacy contract of this endpoint stays stable.
        """
        response = []
        for strategy in all_engine_strategies():
            hash_version = strategy._generate_hash_of_calculate_points()
            response.append(
                {
                    "id": strategy.id,
                    "name": strategy.get_strategy_name(),
                    "description": strategy.get_strategy_description(),
                    "version": strategy.get_strategy_version(),
                    "variables": strategy.get_variables(),
                    "hash_version": hash_version,
                }
            )
        return response

    def get_strategy_by_id(self, id) -> dict[str, Any]:
        """
        Retrieves a built-in strategy by its ID.
        """
        for strategy in self.list_all_strategies():
            if strategy["id"] == id:
                return strategy
        raise NotFoundError(detail=f"Strategy not found with id: {id}")

    def get_Class_by_id(self, id) -> Any:
        """
        Retrieves the instance of a built-in strategy by its ID.

        Only handles the registry path; custom DSL strategies need a DB
        round-trip and use the async :meth:`resolve` instead.
        """
        if is_custom_strategy_id(id):
            raise NotFoundError(
                detail=(
                    f"Strategy '{id}' is a DSL strategy. Use the async "
                    "resolve() method (DSL execution arrives in Sprint 4)."
                )
            )
        for strategy in all_engine_strategies():
            if strategy.id == id:
                return strategy
        raise NotFoundError(detail=f"Strategy not found with id: {id}")

    async def resolve(
        self,
        strategy_id: str,
        *,
        realmId: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Single resolution entrypoint for both code paths.

        Returns a small descriptor:
          * for built-ins:
            ``{"kind": "BUILT_IN", "id": "default", "instance": <obj>}``
          * for custom:
            ``{"kind": "DSL_FULL"|"DSL_EXTEND", "id": "custom:<uuid>",
               "definition": <StrategyDefinitionRead>}``

        Execution wiring (``BaseStrategy.calculate_points`` delegating to
        the DSL interpreter when the descriptor is a DSL one) is wired
        in Sprint 4; right now this method is here so call sites can
        already adopt it.
        """
        if is_custom_strategy_id(strategy_id):
            if self._strategy_definition_service is None:
                raise NotFoundError(
                    detail=(
                        "Custom strategy resolution is unavailable: "
                        "StrategyDefinitionService not wired."
                    )
                )
            uuid_part = parse_custom_strategy_id(strategy_id)
            definition = await self._strategy_definition_service.get_strategy(
                id=uuid_part, realmId=realmId
            )
            return {
                "kind": definition.type,
                "id": strategy_id,
                "definition": definition,
            }
        instance = self.get_Class_by_id(strategy_id)
        return {
            "kind": "BUILT_IN",
            "id": strategy_id,
            "instance": instance,
        }
