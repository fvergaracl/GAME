"""Shared attribute contract for the ``UserPointsService`` mixins.

The mixins in this package are never instantiated on their own; they are
composed into :class:`app.services.user_points_service.UserPointsService`,
whose ``__init__`` assigns the repositories and the strategy service. Declaring
those collaborators here lets each mixin type-check ``self.<collaborator>``
accesses without depending on the others.
"""

from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_game_config_repository import UserGameConfigRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.repository.wallet_repository import WalletRepository
from app.repository.wallet_transaction_repository import WalletTransactionRepository
from app.services.strategy_service import StrategyService

# Cap parallel fan-out so a request over a large user/task list cannot
# saturate the connection pool (pool_size=20, max_overflow=40).
FANOUT_LIMIT = 20


class UserPointsContext:
    """Collaborators wired by ``UserPointsService.__init__``.

    Mixins inherit from this so the attributes they read are typed; the
    concrete values are set by the composed service, not here.
    """

    user_points_repository: UserPointsRepository
    users_repository: UserRepository
    users_game_config_repository: UserGameConfigRepository
    game_repository: GameRepository
    task_repository: TaskRepository
    wallet_repository: WalletRepository
    wallet_transaction_repository: WalletTransactionRepository
    strategy_service: StrategyService
