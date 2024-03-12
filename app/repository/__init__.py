from app.repository.base_repository import BaseRepository
from app.repository.game_params_repository import GameParamsRepository
from app.repository.game_repository import GameRepository
from app.repository.task_params_repository import TaskParamsRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.repository.wallet_repository import WalletRepository
from app.repository.wallet_transaction_repository import \
    WalletTransactionRepository

__all__ = [
    "BaseRepository",
    "GameRepository",
    "TaskParamsRepository",
    "TaskRepository",
    "UserRepository",
    "UserPointsRepository",
    "WalletRepository",
    "WalletTransactionRepository",
    "GameParamsRepository",
]
