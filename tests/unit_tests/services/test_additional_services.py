from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repository.abuse_limit_counter_repository import AbuseLimitCounterRepository
from app.repository.api_requests_repository import ApiRequestsRepository
from app.repository.game_params_repository import GameParamsRepository
from app.repository.kpi_metrics_repository import KpiMetricsRepository
from app.repository.logs_repository import LogsRepository
from app.repository.oauth_users_repository import OAuthUsersRepository
from app.repository.uptime_logs_repository import UptimeLogsRepository
from app.repository.user_interactions_repository import UserInteractionsRepository
from app.services.abuse_prevention_service import AbusePreventionService
from app.services.api_requests_service import ApiRequestsService
from app.services.game_params_service import GameParamsService
from app.services.kpi_metrics_service import KpiMetricsService
from app.services.logs_service import LogsService
from app.services.oauth_users_service import OAuthUsersService
from app.services.uptime_logs_service import UptimeLogsService
from app.services.user_interactions_service import UserInteractionsService


def test_light_services_set_expected_repository_attributes():
    abuse_limit_counter_repository = MagicMock(spec=AbuseLimitCounterRepository)
    api_requests_repository = MagicMock(spec=ApiRequestsRepository)
    game_params_repository = MagicMock(spec=GameParamsRepository)
    kpi_metrics_repository = MagicMock(spec=KpiMetricsRepository)
    logs_repository = MagicMock(spec=LogsRepository)
    uptime_logs_repository = MagicMock(spec=UptimeLogsRepository)
    user_interactions_repository = MagicMock(spec=UserInteractionsRepository)

    abuse_prevention_service = AbusePreventionService(abuse_limit_counter_repository)
    api_requests_service = ApiRequestsService(api_requests_repository)
    game_params_service = GameParamsService(game_params_repository)
    kpi_metrics_service = KpiMetricsService(kpi_metrics_repository)
    logs_service = LogsService(logs_repository)
    uptime_logs_service = UptimeLogsService(uptime_logs_repository)
    user_interactions_service = UserInteractionsService(user_interactions_repository)

    assert (
        abuse_prevention_service.abuse_limit_counter_repository
        is abuse_limit_counter_repository
    )
    assert api_requests_service.api_requests_repository is api_requests_repository
    assert api_requests_service._repository is api_requests_repository
    assert game_params_service.game_params_repository is game_params_repository
    assert game_params_service._repository is game_params_repository
    assert kpi_metrics_service.kpi_metrics_repository is kpi_metrics_repository
    assert kpi_metrics_service._repository is kpi_metrics_repository
    assert logs_service.logs_repository is logs_repository
    assert logs_service._repository is logs_repository
    assert uptime_logs_service.uptime_logs_repository is uptime_logs_repository
    assert uptime_logs_service._repository is uptime_logs_repository
    assert user_interactions_service.user_interactions_repository is user_interactions_repository
    assert user_interactions_service._repository is user_interactions_repository


@pytest.mark.asyncio
async def test_oauth_users_service_get_user_by_sub_delegates_to_repository():
    oauth_users_repository = MagicMock(spec=OAuthUsersRepository)
    oauth_users_repository.get_user_by_sub = AsyncMock(return_value={"id": "u-1"})
    service = OAuthUsersService(oauth_users_repository)

    result = await service.get_user_by_sub("sub-1")

    oauth_users_repository.get_user_by_sub.assert_awaited_once_with("sub-1")
    assert result == {"id": "u-1"}
