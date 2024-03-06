from app.repository.base_repository import BaseRepository
from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.repository.game_params_repository import GameParamsRepository
from app.repository.game_repository import GameRepository
from app.repository.strategy_repository import StrategyRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.repository.wallet_repository import WalletRepository
from app.repository.wallet_transaction_repository import WalletTransactionRepository


class EngineRepository(BaseRepository):

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model_game_params_repository=GameParamsRepository,
        model_game_repository=GameRepository,
        model_strategy_repository=StrategyRepository,
        model_task_repository=TaskRepository,
        model_user_points_repository=UserPointsRepository,
        model_user_repository=UserRepository,
        model_wallet_repository=WalletRepository,
        model_wallet_transaction_repository=WalletTransactionRepository
    ) -> None:
        self.model_game_params_repository = model_game_params_repository
        self.model_game_repository = model_game_repository
        self.model_strategy_repository = model_strategy_repository
        self.model_task_repository = model_task_repository
        self.model_user_points_repository = model_user_points_repository
        self.model_user_repository = model_user_repository
        self.model_wallet_repository = model_wallet_repository
        self.model_wallet_transaction_repository = model_wallet_transaction_repository
        super().__init__(
            session_factory,
            model_game_params_repository,
            model_game_repository,
            model_strategy_repository,
            model_task_repository,
            model_user_points_repository,
            model_user_repository,
            model_wallet_repository,
            model_wallet_transaction_repository
        )
