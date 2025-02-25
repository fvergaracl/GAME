from dependency_injector import containers, providers

from app.core.config import configs
from app.core.database import Database

# pylint: disable=unused-wildcard-import
from app.repository import (
    ApiKeyRepository,
    GameParamsRepository,
    GameRepository,
    TaskParamsRepository,
    TaskRepository,
    UserActionsRepository,
    UserPointsRepository,
    UserGameConfigRepository,
    UserRepository,
    WalletRepository,
    WalletTransactionRepository,
    ApiRequestsRepository,
    KpiMetricsRepository,
    UptimeLogsRepository,
    UserInteractionsRepository,
    dashboard_repository,
    oauth_users_repository,
    logs_repository,
)
from app.services import (
    ApiKeyService,
    GameParamsService,
    GameService,
    StrategyService,
    TaskService,
    UserActionsService,
    UserPointsService,
    UserGameConfigService,
    UserService,
    WalletService,
    WalletTransactionService,
    ApiRequestsService,
    KpiMetricsService,
    UptimeLogsService,
    UserInteractionsService,
    dashboard_service,
    oauth_users_service,
    logs_service,
)


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
        user_actions_repository (providers.Factory): Factory provider for
          UserActionsRepository.
        user_points_repository (providers.Factory): Factory provider for
          UserPointsRepository.
        user_repository (providers.Factory): Factory provider for
          UserRepository.
        wallet_repository (providers.Factory): Factory provider for
          WalletRepository.
        wallet_transaction_repository (providers.Factory): Factory provider
          for WalletTransactionRepository.
        apikey_repository (providers.Factory): Factory provider for
          ApiKeyRepository.
        api_requests_repository (providers.Factory): Factory provider for
          ApiRequestsRepository.
        kpi_metrics_repository (providers.Factory): Factory provider for
          KpiMetricsRepository.
        uptime_logs_repository (providers.Factory): Factory provider for
          UptimeLogsRepository.
        user_interactions_repository (providers.Factory): Factory provider for
          UserInteractionsRepository.
        dashboard_repository (providers.Factory): Factory provider for
          DashboardRepository.
        oauth_users_repository (providers.Factory): Factory provider for
          OAuthUsersRepository.
        logs_repository (providers.Factory): Factory provider for
          LogsRepository.
        game_params_service (providers.Factory): Factory provider for
          GameParamsService.
        strategy_service (providers.Factory): Factory provider for
          StrategyService.
        game_service (providers.Factory): Factory provider for GameService.
        task_service (providers.Factory): Factory provider for TaskService.
        user_points_service (providers.Factory): Factory provider for
          UserPointsService.
        user_service (providers.Factory): Factory provider for UserService.
        user_game_config_service (providers.Factory): Factory provider for
          UserGameConfigService.
        wallet_service (providers.Factory): Factory provider for WalletService.
        wallet_transaction_service (providers.Factory): Factory provider for
          WalletTransactionService.
        apikey_service (providers.Factory): Factory provider for
          ApiKeyService.
        api_requests_service (providers.Factory): Factory provider for
          ApiRequestsService.
        kpi_metrics_service (providers.Factory): Factory provider for
          KpiMetricsService.
        uptime_logs_service (providers.Factory): Factory provider for
          UptimeLogsService.
        user_interactions_service (providers.Factory): Factory provider for
          UserInteractionsService.
        user_game_config_service (providers.Factory): Factory provider for
            UserGameConfigService.
        dashboard_service (providers.Factory): Factory provider for
          DashboardService.
        oauth_users_service (providers.Factory): Factory provider for
          OAuthUsersService.
        logs_service (providers.Factory): Factory provider for LogsService.
    """

    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.v1.endpoints.games",
            "app.api.v1.endpoints.tasks",
            "app.api.v1.endpoints.strategy",
            "app.api.v1.endpoints.userPoints",
            "app.api.v1.endpoints.users",
            "app.api.v1.endpoints.wallet",
            "app.api.v1.endpoints.apikey",
            "app.api.v1.endpoints.kpi",
            "app.api.v1.endpoints.dashboard",
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

    user_actions_repository = providers.Factory(
        UserActionsRepository, session_factory=db.provided.session
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

    apikey_repository = providers.Factory(
        ApiKeyRepository, session_factory=db.provided.session
    )

    api_requests_repository = providers.Factory(
        ApiRequestsRepository, session_factory=db.provided.session
    )

    kpi_metrics_repository = providers.Factory(
        KpiMetricsRepository, session_factory=db.provided.session
    )

    uptime_logs_repository = providers.Factory(
        UptimeLogsRepository, session_factory=db.provided.session
    )

    user_interactions_repository = providers.Factory(
        UserInteractionsRepository, session_factory=db.provided.session
    )

    user_game_config_repository = providers.Factory(
        UserGameConfigRepository, session_factory=db.provided.session
    )
    dashboard_repository = providers.Factory(
        dashboard_repository.DashboardRepository,
        session_factory=db.provided.session,
    )

    oauth_users_repository = providers.Factory(
        oauth_users_repository.OAuthUsersRepository,
        session_factory=db.provided.session,
    )

    logs_repository = providers.Factory(
        logs_repository.LogsRepository,
        session_factory=db.provided.session,
    )

    # Services (Add in here)

    game_params_service = providers.Factory(
        GameParamsService, game_params_repository=game_params_repository
    )

    strategy_service = providers.Factory(StrategyService)

    game_service = providers.Factory(
        GameService,
        game_repository=game_repository,
        game_params_repository=game_params_repository,
        task_repository=task_repository,
        user_points_repository=user_points_repository,
        strategy_service=strategy_service,
    )

    task_service = providers.Factory(
        TaskService,
        strategy_service=StrategyService,
        task_repository=task_repository,
        game_repository=game_repository,
        user_repository=user_repository,
        user_points_repository=user_points_repository,
        game_params_repository=game_params_repository,
        task_params_repository=task_params_repository,
    )

    user_actions_service = providers.Factory(
        UserActionsService,
        user_actions_repository=user_actions_repository,
        users_repository=user_repository,
        game_repository=game_repository,
        task_repository=task_repository,
    )

    user_points_service = providers.Factory(
        UserPointsService,
        user_points_repository=user_points_repository,
        users_repository=user_repository,
        game_repository=game_repository,
        task_repository=task_repository,
        wallet_repository=wallet_repository,
        wallet_transaction_repository=wallet_transaction_repository,
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
        user_points_repository=user_points_repository,
        task_repository=task_repository,
        wallet_repository=wallet_repository,
        wallet_transaction_repository=wallet_transaction_repository,
    )

    wallet_service = providers.Factory(
        WalletService,
        wallet_repository=wallet_repository,
        user_repository=user_repository,
    )

    wallet_transaction_service = providers.Factory(
        WalletTransactionService,
        wallet_transaction_repository=wallet_transaction_repository,
    )

    apikey_service = providers.Factory(
        ApiKeyService,
        apikey_repository=apikey_repository,
    )

    api_requests_service = providers.Factory(
        ApiRequestsService,
        api_requests_repository=api_requests_repository,
    )

    kpi_metrics_service = providers.Factory(
        KpiMetricsService,
        kpi_metrics_repository=kpi_metrics_repository,
    )

    uptime_logs_service = providers.Factory(
        UptimeLogsService,
        uptime_logs_repository=uptime_logs_repository,
    )

    user_interactions_service = providers.Factory(
        UserInteractionsService,
        user_interactions_repository=user_interactions_repository,
    )

    user_game_config_service = providers.Factory(
        UserGameConfigService,
        user_game_config_repository=user_game_config_repository
    )

    dashboard_service = providers.Factory(
        dashboard_service.DashboardService,
        dashboard_repository=dashboard_repository,
        game_repository=game_repository,
        task_repository=task_repository,
        user_repository=user_repository,
        logs_repository=logs_repository,
        user_points_repository=user_points_repository,
        user_actions_repository=user_actions_repository,
    )

    oauth_users_service = providers.Factory(
        oauth_users_service.OAuthUsersService,
        oauth_users_repository=oauth_users_repository,
    )

    logs_service = providers.Factory(
        logs_service.LogsService,
        logs_repository=logs_repository,
    )
