from unittest.mock import MagicMock

import pytest

from app.model.api_key import ApiKey
from app.model.api_requests import ApiRequests
from app.model.abuse_limit_counter import AbuseLimitCounter
from app.model.kpi_metrics import KpiMetrics
from app.model.logs import Logs
from app.model.oauth_users import OAuthUsers
from app.model.uptime_logs import UptimeLogs
from app.model.user_interactions import UserInteractions
from app.repository.api_requests_repository import ApiRequestsRepository
from app.repository.abuse_limit_counter_repository import AbuseLimitCounterRepository
from app.repository.apikey_repository import ApiKeyRepository
from app.repository.kpi_metrics_repository import KpiMetricsRepository
from app.repository.logs_repository import LogsRepository
from app.repository.oauth_users_repository import OAuthUsersRepository
from app.repository.uptime_logs_repository import UptimeLogsRepository
from app.repository.user_game_config_repository import UserGameConfigRepository
from app.repository.user_interactions_repository import UserInteractionsRepository


def _build_session_factory():
    session = MagicMock()
    context_manager = MagicMock()
    context_manager.__enter__.return_value = session
    context_manager.__exit__.return_value = False
    session_factory = MagicMock(return_value=context_manager)
    return session_factory, session


def test_light_repositories_set_expected_default_models():
    session_factory, _ = _build_session_factory()

    assert (
        AbuseLimitCounterRepository(session_factory=session_factory).model
        is AbuseLimitCounter
    )
    assert ApiRequestsRepository(session_factory=session_factory).model is ApiRequests
    assert ApiKeyRepository(session_factory=session_factory).model is ApiKey
    assert KpiMetricsRepository(session_factory=session_factory).model is KpiMetrics
    assert LogsRepository(session_factory=session_factory).model is Logs
    assert OAuthUsersRepository(session_factory=session_factory).model is OAuthUsers
    assert UptimeLogsRepository(session_factory=session_factory).model is UptimeLogs
    assert (
        UserInteractionsRepository(session_factory=session_factory).model
        is UserInteractions
    )


def test_apikey_repository_read_all_caps_page_size_and_applies_pagination():
    session_factory, session = _build_session_factory()
    repository = ApiKeyRepository(session_factory=session_factory)

    query = MagicMock()
    session.query.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.offset.return_value = query
    query.all.return_value = ["api-key-1"]

    result = repository.read_all(page=2, page_size=1000)

    session.query.assert_called_once_with(repository.model)
    query.order_by.assert_called_once()
    query.limit.assert_called_once_with(100)
    query.offset.assert_called_once_with(100)
    assert result == ["api-key-1"]


@pytest.mark.asyncio
async def test_oauth_users_repository_get_user_by_sub_filters_and_returns_first():
    session_factory, session = _build_session_factory()
    repository = OAuthUsersRepository(session_factory=session_factory)

    query = MagicMock()
    session.query.return_value = query
    query.filter_by.return_value = query
    query.first.return_value = {"provider_user_id": "sub-1"}

    result = await repository.get_user_by_sub("sub-1")

    session.query.assert_called_once_with(repository.model)
    query.filter_by.assert_called_once_with(provider_user_id="sub-1")
    query.first.assert_called_once()
    assert result == {"provider_user_id": "sub-1"}


def test_user_game_config_repository_get_all_users_by_game_id():
    session_factory, session = _build_session_factory()
    repository = UserGameConfigRepository(session_factory=session_factory)

    query = MagicMock()
    session.query.return_value = query
    query.filter_by.return_value = query
    query.all.return_value = [{"userId": "u-1"}]

    result = repository.get_all_users_by_gameId("game-1")

    session.query.assert_called_once_with(repository.model)
    query.filter_by.assert_called_once_with(gameId="game-1")
    query.all.assert_called_once()
    assert result == [{"userId": "u-1"}]
