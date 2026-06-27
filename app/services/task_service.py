"""Public entry point for task operations.

``TaskService`` composes three focused mixins (see :mod:`app.services.task`)
so its read, write and points-by-task concerns live in separate modules
without changing the single DI-injected class that endpoints depend on:

* :class:`TaskQueryMixin` - read-only task lookups and listings.
* :class:`TaskMutationMixin` - the create/patch/delete/duplicate write path.
* :class:`TaskPointsMixin` - points-by-task read queries.
"""

from typing import Optional

from app.repository.game_params_repository import GameParamsRepository
from app.repository.game_repository import GameRepository
from app.repository.task_params_repository import TaskParamsRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.services.base_service import BaseService
from app.services.strategy_definition_service import StrategyDefinitionService
from app.services.strategy_service import StrategyService
from app.services.task import TaskMutationMixin, TaskPointsMixin, TaskQueryMixin


class TaskService(
    BaseService,
    TaskQueryMixin,
    TaskMutationMixin,
    TaskPointsMixin,
):
    """
    Service class for managing tasks.

    Attributes:
        strategy_service (StrategyService): Service instance for strategies.
        task_repository (TaskRepository): Repository instance for tasks.
        game_repository (GameRepository): Repository instance for games.
        user_repository (UserRepository): Repository instance for users.
        user_points_repository (UserPointsRepository): Repository instance for
          user points.
        game_params_repository (GameParamsRepository): Repository instance for
          game parameters.
        task_params_repository (TaskParamsRepository): Repository instance for
          task parameters.
    """

    def __init__(
        self,
        strategy_service: StrategyService,
        task_repository: TaskRepository,
        game_repository: GameRepository,
        user_repository: UserRepository,
        user_points_repository: UserPointsRepository,
        game_params_repository: GameParamsRepository,
        task_params_repository: TaskParamsRepository,
        strategy_definition_service: Optional[StrategyDefinitionService] = None,
    ) -> None:
        """
        Initializes the TaskService with the provided repositories and
          services.

        ``strategy_definition_service`` is optional so existing call sites
        and tests that don't exercise ``custom:`` strategyIds keep
        working. Required for :meth:`patch_task_by_id` to validate
        ``custom:`` ids against the persistent registry.
        """
        self.strategy_service = strategy_service
        self.task_repository = task_repository
        self.game_repository = game_repository
        self.user_repository = user_repository
        self.user_points_repository = user_points_repository
        self.game_params_repository = game_params_repository
        self.task_params_repository = task_params_repository
        self.strategy_definition_service = strategy_definition_service
        super().__init__(task_repository)
