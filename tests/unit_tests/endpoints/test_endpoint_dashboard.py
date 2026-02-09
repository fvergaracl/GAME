from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.endpoints import dashboard


def _api_key_header(api_key="api-key-1"):
    return SimpleNamespace(data=SimpleNamespace(apiKey=api_key))


@pytest.mark.asyncio
async def test_get_dashboard_summary_with_token_creates_oauth_user_and_returns_schema():
    service = MagicMock()
    service.get_dashboard_summary.return_value = {
        "new_users": [{"label": "2026-02-01", "count": 2}],
        "games_opened": [{"label": "2026-02-01", "count": 1}],
        "points_earned": [{"label": "2026-02-01", "count": 100}],
        "actions_performed": [{"label": "2026-02-01", "count": 4}],
    }
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub.return_value = None
    service_oauth.add = AsyncMock()

    with patch(
        "app.api.v1.endpoints.dashboard.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(data={"sub": "oauth-user-1"})),
    ), patch("app.api.v1.endpoints.dashboard.add_log", new=AsyncMock()) as mock_add_log:
        result = await dashboard.get_dashboard_summary(
            start_date="2026-02-01",
            end_date="2026-02-02",
            group_by="day",
            service=service,
            service_log=service_log,
            service_oauth=service_oauth,
            token="Bearer token",
            api_key_header=_api_key_header(),
        )

    assert result.new_users[0].count == 2
    assert result.games_opened[0].count == 1
    assert result.points_earned[0].count == 100
    assert result.actions_performed[0].count == 4
    service.get_dashboard_summary.assert_called_once_with(
        "2026-02-01", "2026-02-02", "day"
    )
    service_oauth.add.assert_awaited_once()
    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_get_dashboard_summary_without_token_skips_oauth_validation():
    service = MagicMock()
    service.get_dashboard_summary.return_value = {
        "new_users": [],
        "games_opened": [],
        "points_earned": [],
        "actions_performed": [],
    }
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub.return_value = None
    service_oauth.add = AsyncMock()

    with patch(
        "app.api.v1.endpoints.dashboard.valid_access_token",
        new=AsyncMock(),
    ) as mock_valid_access_token, patch(
        "app.api.v1.endpoints.dashboard.add_log", new=AsyncMock()
    ) as mock_add_log:
        result = await dashboard.get_dashboard_summary(
            start_date=None,
            end_date=None,
            group_by=None,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token=None,
            api_key_header=_api_key_header(),
        )

    assert result.new_users == []
    assert result.games_opened == []
    assert result.points_earned == []
    assert result.actions_performed == []
    mock_valid_access_token.assert_not_awaited()
    service_oauth.add.assert_not_awaited()
    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_dashboard_summary_logs_with_token_creates_oauth_user_and_returns_schema():
    service = MagicMock()
    service.get_dashboard_summary_logs.return_value = {
        "info": [{"label": "2026-02-01", "count": 7}],
        "success": [{"label": "2026-02-01", "count": 5}],
        "error": [{"label": "2026-02-01", "count": 1}],
    }
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub.return_value = None
    service_oauth.add = AsyncMock()

    with patch(
        "app.api.v1.endpoints.dashboard.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(data={"sub": "oauth-user-2"})),
    ), patch("app.api.v1.endpoints.dashboard.add_log", new=AsyncMock()) as mock_add_log:
        result = await dashboard.get_dashboard_summary_logs(
            start_date="2026-02-01",
            end_date="2026-02-28",
            group_by="month",
            service=service,
            service_log=service_log,
            service_oauth=service_oauth,
            token="Bearer token",
            api_key_header=_api_key_header(),
        )

    assert result.info[0].count == 7
    assert result.success[0].count == 5
    assert result.error[0].count == 1
    service.get_dashboard_summary_logs.assert_called_once_with(
        "2026-02-01", "2026-02-28", "month"
    )
    service_oauth.add.assert_awaited_once()
    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_get_dashboard_summary_logs_without_token_skips_oauth_validation():
    service = MagicMock()
    service.get_dashboard_summary_logs.return_value = {
        "info": [],
        "success": [],
        "error": [],
    }
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub.return_value = None
    service_oauth.add = AsyncMock()

    with patch(
        "app.api.v1.endpoints.dashboard.valid_access_token",
        new=AsyncMock(),
    ) as mock_valid_access_token, patch(
        "app.api.v1.endpoints.dashboard.add_log", new=AsyncMock()
    ) as mock_add_log:
        result = await dashboard.get_dashboard_summary_logs(
            start_date=None,
            end_date=None,
            group_by=None,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token=None,
            api_key_header=_api_key_header(),
        )

    assert result.info == []
    assert result.success == []
    assert result.error == []
    mock_valid_access_token.assert_not_awaited()
    service_oauth.add.assert_not_awaited()
    mock_add_log.assert_awaited_once()
