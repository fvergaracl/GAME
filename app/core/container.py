from dependency_injector import containers, providers

from app.core.config import configs
from app.core.database import Database
# pylint: disable=unused-wildcard-import
from app.repository import *
from app.services import *


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.v1.endpoints.games",
            "app.api.v1.endpoints.tasks",
        ]
    )

    db = providers.Singleton(Database, db_url=configs.DATABASE_URI)

    # Repository (Add in here)

    game_repository = providers.Factory(
        GameRepository, session_factory=db.provided.session)
    game_params_repository = providers.Factory(
        GameParamsRepository, session_factory=db.provided.session)

    strategy_repository = providers.Factory(
        StrategyRepository, session_factory=db.provided.session)

    task_repository = providers.Factory(
        TaskRepository, session_factory=db.provided.session)

    user_points_repository = providers.Factory(
        UserPointsRepository, session_factory=db.provided.session)

    user_repository = providers.Factory(
        UserRepository, session_factory=db.provided.session)

    wallet_repository = providers.Factory(
        WalletRepository, session_factory=db.provided.session)

    wallet_transaction_repository = providers.Factory(
        WalletTransactionRepository, session_factory=db.provided.session)

    # Services (Add in here)

    game_service = providers.Factory(
        GameService,
        game_repository=game_repository,
        game_params_repository=game_params_repository
    )

    game_params_service = providers.Factory(
        GameParamsService,
        game_params_repository=game_params_repository
    )

    strategy_service = providers.Factory(
        StrategyService,
        strategy_repository=strategy_repository
    )

    task_service = providers.Factory(
        TaskService,
        task_repository=task_repository,
        game_repository=game_repository
    )

    user_points_service = providers.Factory(
        UserPointsService,
        user_points_repository=user_points_repository
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository
    )

    wallet_service = providers.Factory(
        WalletService,
        wallet_repository=wallet_repository
    )

    wallet_transaction_service = providers.Factory(
        WalletTransactionService,
        wallet_transaction_repository=wallet_transaction_repository
    )
