"""Shared collaborators + helper for the ``TaskService`` mixins.

The mixins in this package are never instantiated on their own; they are
composed into :class:`app.services.task_service.TaskService`, whose
``__init__`` assigns the repositories and services. Declaring those
collaborators here lets each mixin type-check ``self.<collaborator>``
accesses without importing one another.
"""

from typing import Optional

from app.repository.game_params_repository import GameParamsRepository
from app.repository.game_repository import GameRepository
from app.repository.task_params_repository import TaskParamsRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.services.strategy_definition_service import StrategyDefinitionService
from app.services.strategy_service import StrategyService


class TaskServiceContext:
    """Collaborators wired by ``TaskService.__init__``.

    Mixins inherit from this so the attributes they read are typed; the
    concrete values are set by the composed service, not here.
    """

    strategy_service: StrategyService
    task_repository: TaskRepository
    game_repository: GameRepository
    user_repository: UserRepository
    user_points_repository: UserPointsRepository
    game_params_repository: GameParamsRepository
    task_params_repository: TaskParamsRepository
    strategy_definition_service: Optional[StrategyDefinitionService]


def apply_strategy_variable_overrides(params, strategy_data) -> None:
    """Coerce each param value to its strategy-variable type and, when the
    coerced type matches the variable's, override the strategy's default
    variable with it -- mutating both ``param.value`` and
    ``strategy_data["variables"]`` in place.

    Extracted verbatim from the five identical loops the original
    ``TaskService`` inlined across its read/create methods; ``params`` may be
    ``None``/empty (mirroring the previous ``if params:`` guards).
    """
    if not params:
        return
    for param in params:
        if param.key in strategy_data["variables"]:
            try:
                param.value = int(param.value)
            except ValueError:
                try:
                    param.value = float(param.value)
                except ValueError:
                    pass
            type_param = type(param.value)
            type_strategy_variable = type(strategy_data["variables"][param.key])
            if type_param == type_strategy_variable:
                strategy_data["variables"][param.key] = param.value
