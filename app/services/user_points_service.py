"""Public entry point for user-points operations.

``UserPointsService`` composes four focused mixins (see
:mod:`app.services.user_points`) so its read, write, simulation and
persistence concerns live in separate modules without changing the single
DI-injected class that endpoints and strategy engines depend on:

* :class:`PointsQueryMixin` - read-only aggregations and lookups.
* :class:`PointsAssignmentMixin` - the scoring/write path (also brings the
  persistence helpers it builds on).
* :class:`PointsSimulationMixin` - non-persisting simulation of built-ins.
* :class:`PointsPersistenceMixin` - the atomic points/wallet/transaction write.
"""

import logging

from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_game_config_repository import UserGameConfigRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.repository.wallet_repository import WalletRepository
from app.repository.wallet_transaction_repository import WalletTransactionRepository
from app.services.base_service import BaseService
from app.services.strategy_service import StrategyService
from app.services.user_points import (
    PointsAssignmentMixin,
    PointsQueryMixin,
    PointsSimulationMixin,
)

logger = logging.getLogger(__name__)


class UserPointsService(
    BaseService,
    PointsQueryMixin,
    PointsAssignmentMixin,
    PointsSimulationMixin,
):
    def __init__(
        self,
        user_points_repository: UserPointsRepository,
        users_repository: UserRepository,
        users_game_config_repository: UserGameConfigRepository,
        game_repository: GameRepository,
        task_repository: TaskRepository,
        wallet_repository: WalletRepository,
        wallet_transaction_repository: WalletTransactionRepository,
        strategy_service: "StrategyService | None" = None,
    ) -> None:
        self.user_points_repository = user_points_repository
        self.users_repository = users_repository
        self.users_game_config_repository = users_game_config_repository
        self.game_repository = game_repository
        self.task_repository = task_repository
        self.wallet_repository = wallet_repository
        self.wallet_transaction_repository = wallet_transaction_repository
        # When constructed via DI (the production path) the container
        # injects a fully-wired StrategyService that can resolve
        # ``custom:<uuid>`` ids against the DB. The no-arg fallback
        # preserves the legacy behaviour for tests that build this
        # service positionally and monkey-patch ``self.strategy_service``.
        self.strategy_service = strategy_service or StrategyService()
        super().__init__(user_points_repository)
