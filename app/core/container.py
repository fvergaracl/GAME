from dependency_injector import containers, providers

from app.core.config import configs
from app.core.database import Database
# pylint: disable=unused-wildcard-import
from app.repository import (GameParamsRepository, GameRepository,
                            TaskRepository,
                            UserPointsRepository, UserRepository,
                            WalletRepository, WalletTransactionRepository,
                            TaskParamsRepository)
from app.services import (GameParamsService, GameService,
                          TaskService, UserPointsService,
                          UserService, WalletService, WalletTransactionService,
                          StrategyService)


class Container(containers.DeclarativeContainer):
    """
    Dependency injection container for managing application dependencies.

    Attributes:
        wiring_config (containers.WiringConfiguration): Configuration for
          wiring dependencies to modules.
        db (providers.Singleton): Singleton provider for the Database.
        game_repository (providers.Factory): Factory provider for
          GameRepository.
        game_params_repository (providers.Factory): Factory provider for
          GameParamsRepository.
        task_params_repository (providers.Factory): Factory provider for
          TaskParamsRepository.
        task_repository (providers.Factory): Factory provider for
          TaskRepository.
        user_points_repository (providers.Factory): Factory provider for
          UserPointsRepository.
        user_repository (providers.Factory): Factory provider for
          UserRepository.
        wallet_repository (providers.Factory): Factory provider for
          WalletRepository.
        wallet_transaction_repository (providers.Factory): Factory provider
          for WalletTransactionRepository.
        game_params_service (providers.Factory): Factory provider for
          GameParamsService.
        strategy_service (providers.Factory): Factory provider for
          StrategyService.
        game_service (providers.Factory): Factory provider for GameService.
        task_service (providers.Factory): Factory provider for TaskService.
        user_points_service (providers.Factory): Factory provider for
          UserPointsService.
        user_service (providers.Factory): Factory provider for UserService.
        wallet_service (providers.Factory): Factory provider for WalletService.
        wallet_transaction_service (providers.Factory): Factory provider for
          WalletTransactionService.
    """
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.v1.endpoints.games",
            "app.api.v1.endpoints.tasks",
            "app.api.v1.endpoints.strategy",
            "app.api.v1.endpoints.userPoints",
            "app.api.v1.endpoints.users",
            "app.api.v1.endpoints.wallet",
        ]
    )

    db = providers.Singleton(Database, db_url=configs.DATABASE_URI)

    # Repository (Add in here)

    game_repository = providers.Factory(
        GameRepository, session_factory=db.provided.session
    )
    game_params_repository = providers.Factory(
        GameParamsRepository, session_factory=db.provided.session
    )

    task_params_repository = providers.Factory(
        TaskParamsRepository, session_factory=db.provided.session
    )
    task_repository = providers.Factory(
        TaskRepository, session_factory=db.provided.session
    )

    user_points_repository = providers.Factory(
        UserPointsRepository, session_factory=db.provided.session
    )

    user_repository = providers.Factory(
        UserRepository, session_factory=db.provided.session
    )

    wallet_repository = providers.Factory(
        WalletRepository, session_factory=db.provided.session
    )

    wallet_transaction_repository = providers.Factory(
        WalletTransactionRepository, session_factory=db.provided.session
    )

    # Services (Add in here)

    game_params_service = providers.Factory(  # noqa
        GameParamsService, game_params_repository=game_params_repository
    )

    strategy_service = providers.Factory(  # noqa
        StrategyService
    )

    game_service = providers.Factory(  # noqa
        GameService,
        game_repository=game_repository,
        game_params_repository=game_params_repository,
        task_repository=task_repository,
        strategy_service=strategy_service,
    )

    task_service = providers.Factory(  # noqa
        TaskService,
        strategy_service=StrategyService,
        task_repository=task_repository,
        game_repository=game_repository,
        user_repository=user_repository,
        user_points_repository=user_points_repository,
        game_params_repository=game_params_repository,
        task_params_repository=task_params_repository,
    )

    user_points_service = providers.Factory(  # noqa
        UserPointsService,
        user_points_repository=user_points_repository,
        users_repository=user_repository,
        game_repository=game_repository,
        task_repository=task_repository,
        wallet_repository=wallet_repository,
        wallet_transaction_repository=wallet_transaction_repository,
    )

    user_service = providers.Factory(  # noqa
        UserService,
        user_repository=user_repository,
        user_points_repository=user_points_repository,
        task_repository=task_repository,
        wallet_repository=wallet_repository,
        wallet_transaction_repository=wallet_transaction_repository,
    )

    wallet_service = providers.Factory(  # noqa
        WalletService,
        wallet_repository=wallet_repository,
        user_repository=user_repository,
    )

    wallet_transaction_service = providers.Factory(  # noqa
        WalletTransactionService,
        wallet_transaction_repository=wallet_transaction_repository,
    )
