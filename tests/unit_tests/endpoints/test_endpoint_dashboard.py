from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.endpoints import dashboard
from app.middlewares.auth_context import AuditLogger, AuthContext


def _audit(api_key="api-key-1", oauth_user_id=None):
    return AuditLogger(
        "dashboard",
        MagicMock(),
        AuthContext(
            api_key=api_key,
            oauth_user_id=oauth_user_id,
            is_admin=False,
            token_data={"sub": oauth_user_id} if oauth_user_id else None,
        ),
    )


@pytest.mark.asyncio
async def test_get_dashboard_summary_with_token_creates_oauth_user_and_returns_schema():
    service = AsyncMock()
    service.get_dashboard_summary.return_value = {
        "new_users": [{"label": "2026-02-01", "count": 2}],
        "games_opened": [{"label": "2026-02-01", "count": 1}],
        "points_earned": [{"label": "2026-02-01", "count": 100}],
        "actions_performed": [{"label": "2026-02-01", "count": 4}],
    }
    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        result = await dashboard.get_dashboard_summary(
            start_date="2026-02-01",
            end_date="2026-02-02",
            group_by="day",
            service=service,
            audit=_audit(oauth_user_id="oauth-user-1"),
        )

    assert result.new_users[0].count == 2
    assert result.games_opened[0].count == 1
    assert result.points_earned[0].count == 100
    assert result.actions_performed[0].count == 4
    service.get_dashboard_summary.assert_called_once_with(
        "2026-02-01", "2026-02-02", "day"
    )
    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_dashboard_summary_without_token_skips_oauth_validation():
    service = AsyncMock()
    service.get_dashboard_summary.return_value = {
        "new_users": [],
        "games_opened": [],
        "points_earned": [],
        "actions_performed": [],
    }
    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        result = await dashboard.get_dashboard_summary(
            start_date=None,
            end_date=None,
            group_by=None,
            service=service,
            audit=_audit(),
        )

    assert result.new_users == []
    assert result.games_opened == []
    assert result.points_earned == []
    assert result.actions_performed == []
    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_dashboard_summary_logs_with_token_creates_oauth_user_and_returns_schema():
    service = AsyncMock()
    service.get_dashboard_summary_logs.return_value = {
        "info": [{"label": "2026-02-01", "count": 7}],
        "success": [{"label": "2026-02-01", "count": 5}],
        "error": [{"label": "2026-02-01", "count": 1}],
    }
    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        result = await dashboard.get_dashboard_summary_logs(
            start_date="2026-02-01",
            end_date="2026-02-28",
            group_by="month",
            service=service,
            audit=_audit(oauth_user_id="oauth-user-2"),
        )

    assert result.info[0].count == 7
    assert result.success[0].count == 5
    assert result.error[0].count == 1
    service.get_dashboard_summary_logs.assert_called_once_with(
        "2026-02-01", "2026-02-28", "month"
    )
    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_dashboard_summary_logs_without_token_skips_oauth_validation():
    service = AsyncMock()
    service.get_dashboard_summary_logs.return_value = {
        "info": [],
        "success": [],
        "error": [],
    }
    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        result = await dashboard.get_dashboard_summary_logs(
            start_date=None,
            end_date=None,
            group_by=None,
            service=service,
            audit=_audit(),
        )

    assert result.info == []
    assert result.success == []
    assert result.error == []
    mock_add_log.assert_awaited_once()
