from typing import Any, Optional

from app.core.config import configs
from app.core.exceptions import InternalServerError, NotFoundError
from app.engine.all_engine_strategies import all_engine_strategies
from app.engine.base_strategy import BaseStrategy
from app.engine.dsl_interpreter import DslInterpreter
from app.engine.dsl_strategy import DslStrategy
from app.services.base_service import BaseService
from app.services.strategy_definition_service import StrategyDefinitionService

# Prefix used to address DB-persisted custom strategies from the existing
# ``Games.strategyId`` / ``Tasks.strategyId`` columns. Anything without this
# prefix is resolved against the in-process registry, preserving the
# legacy registry behaviour. See the compat-layer notes in the
# roadmap.
CUSTOM_STRATEGY_PREFIX = "custom:"


def is_custom_strategy_id(strategy_id: Optional[str]) -> bool:
    """Return True when ``strategy_id`` addresses a DB-stored strategy."""
    return bool(strategy_id) and strategy_id.startswith(CUSTOM_STRATEGY_PREFIX)


def parse_custom_strategy_id(strategy_id: str) -> str:
    """Strip the ``custom:`` prefix and return the underlying uuid."""
    return strategy_id[len(CUSTOM_STRATEGY_PREFIX) :]


def resolve_realm_id(
    *,
    api_key: Optional[str] = None,
    oauth_user_id: Optional[str] = None,
) -> Optional[str]:
    """
    Tenant-boundary resolver shared by call sites that don't have an
    ``AuthContext`` handy (e.g. ``UserPointsService``).

    Same convention as ``_resolve_realm_id`` in
    ``app/api/v1/endpoints/strategies_custom.py``:

    * API key present → its value *is* the realm.
    * OAuth admin → falls back to ``configs.KEYCLOAK_REALM``.
    * Neither → ``None`` (legacy unauthenticated path; any attempt to load a
      ``custom:`` strategy will then 404, which is the desired
      tenant-isolation behaviour).
    """
    if api_key:
        return api_key
    if oauth_user_id:
        return configs.KEYCLOAK_REALM
    return None


class StrategyService(BaseService):
    """
    Service class for managing strategies.

    Resolution is a two-step routing:

    * built-in strategies (registry-discovered ``BaseStrategy`` subclasses)
      keep their bare id, e.g. ``"default"``.
    * persistent strategies authored from the dashboard live in the
      ``strategydefinition`` table and are addressed as ``"custom:<uuid>"``.
      The resolver returns a thin descriptor for them; the DSL interpreter
      that runs the AST plugs into this same method.
    """

    def __init__(
        self,
        strategy_definition_service: Optional[StrategyDefinitionService] = None,
        *,
        dsl_interpreter: Optional[DslInterpreter] = None,
        analytics_service: Optional[Any] = None,
        execution_observer: Optional[Any] = None,
    ) -> None:
        """
        Initializes the StrategyService.

        ``strategy_definition_service`` is optional so legacy call sites
        that only need built-ins still work after the custom-strategy wiring.
        When it's omitted, attempting to resolve a ``custom:`` id raises
        ``NotFoundError`` with a clear message rather than silently
        crashing.

        ``dsl_interpreter`` and ``analytics_service`` are required to
        instantiate ``DslStrategy`` for ``custom:`` ids.
        They are optional kwargs to preserve the legacy
        ``StrategyService()`` no-arg call style still in use by tests and
        by ``UserPointsService.__init__`` until the container injection
        lands; when missing, ``get_strategy_instance`` raises a precise
        ``InternalServerError`` instead of crashing with ``AttributeError``.
        """
        super().__init__(None)
        self._strategy_definition_service = strategy_definition_service
        self._dsl_interpreter = dsl_interpreter
        self._analytics_service = analytics_service
        # Passed straight through to ``DslStrategy``. Optional
        # so the legacy two-arg construction style in tests still works
        # - metrics + persistence become no-ops in that case.
        self._execution_observer = execution_observer

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
                    "resolve() method."
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
        """Single resolution entrypoint for both code paths.

        Returns a small descriptor. For built-ins::

            {"kind": "BUILT_IN", "id": "default", "instance": <obj>}

        For custom strategies::

            {"kind": "DSL_FULL" | "DSL_EXTEND",
             "id": "custom:<uuid>",
             "definition": <StrategyDefinitionRead>}

        Execution (``BaseStrategy.calculate_points`` delegating to the DSL
        interpreter when the descriptor is a DSL one) plugs into this same
        method.

        Args:
            strategy_id (str): A built-in id (e.g. ``"default"``) or a
                ``"custom:<uuid>"`` id.
            realmId (str, optional): Tenant boundary used to scope custom
                strategy lookups.

        Returns:
            dict: The resolution descriptor described above.

        Raises:
            NotFoundError: If a ``custom:`` id is given but custom-strategy
                resolution is not wired, or the definition is not found.
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

    async def get_strategy_instance(
        self,
        strategy_id: str,
        *,
        realmId: Optional[str] = None,
    ) -> BaseStrategy:
        """
        Single async entrypoint that returns something with
        ``calculate_points(...)`` - either a built-in registry singleton
        or a freshly-constructed ``DslStrategy`` wrapping a DB-persisted
        AST.

        For non-``custom:`` ids this delegates to the sync
        ``get_Class_by_id`` so existing test patches on that method keep
        intercepting. For ``custom:<uuid>`` it fetches the definition
        scoped by ``realmId`` (multi-tenant isolation is enforced at the
        repository layer in ``StrategyDefinitionService.get_strategy``)
        and wires the same shared ``DslInterpreter`` + analytics service
        injected at construction.

        Raises ``InternalServerError`` if the DSL collaborators were not
        wired - a clearer signal than ``AttributeError`` for ops.
        """
        if not is_custom_strategy_id(strategy_id):
            return self.get_Class_by_id(strategy_id)

        if self._strategy_definition_service is None:
            raise NotFoundError(
                detail=(
                    "Custom strategy resolution is unavailable: "
                    "StrategyDefinitionService not wired."
                )
            )
        if self._dsl_interpreter is None or self._analytics_service is None:
            raise InternalServerError(
                detail=(
                    "DslStrategy dependencies (interpreter / analytics) "
                    "are not wired into StrategyService."
                )
            )

        uuid_part = parse_custom_strategy_id(strategy_id)
        definition = await self._strategy_definition_service.get_strategy(
            id=uuid_part, realmId=realmId
        )

        # DSL_EXTEND wraps a built-in parent with pre/post
        # rules. Resolve the parent here (sync registry lookup) and
        # hand it to DslStrategy as a constructor dependency. If the
        # parent id stored in the row no longer references an existing
        # built-in (e.g. removed from the registry between persist and
        # execution), ``get_Class_by_id`` raises NotFoundError with a
        # clear message - better than a silent KeyError at run time.
        parent_strategy = None
        if definition.type == "DSL_EXTEND":
            if not definition.parentStrategyId:
                # The CRUD validator (_validate_payload) enforces this
                # at write time, but defend in depth in case an older
                # row predates the rule.
                raise InternalServerError(
                    detail=(
                        f"Custom strategy {strategy_id} is DSL_EXTEND "
                        "but has no parentStrategyId set."
                    )
                )
            parent_strategy = self.get_Class_by_id(definition.parentStrategyId)

        return DslStrategy(
            definition=definition,
            interpreter=self._dsl_interpreter,
            analytics_service=self._analytics_service,
            parent_strategy=parent_strategy,
            observer=self._execution_observer,
        )
