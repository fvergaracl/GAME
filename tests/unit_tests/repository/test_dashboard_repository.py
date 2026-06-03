"""
Tests for ``DashboardRepository``.

The repository's aggregation queries rely on Postgres-specific functions
(``date_trunc``, ``concat``, ``extract``, ``lpad``) that aiosqlite cannot
execute, so the high-level orchestration is exercised by mocking the
``_execute_query`` boundary. The dispatcher (`_get_group_by_column`) and the
constructor wiring run on the real classes.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import BadRequestError
from app.repository.dashboard_repository import DashboardRepository


@pytest.fixture
def repository(session_factory):
    return DashboardRepository(session_factory=session_factory)


def test_constructor_wires_default_models(repository):
    from app.model.games import Games
    from app.model.logs import Logs
    from app.model.tasks import Tasks
    from app.model.user_actions import UserActions
    from app.model.user_points import UserPoints
    from app.model.users import Users

    assert repository.model_games is Games
    assert repository.model_tasks is Tasks
    assert repository.model_users is Users
    assert repository.model_logs is Logs
    assert repository.model_user_points is UserPoints
    assert repository.model_user_actions is UserActions


def test_get_group_by_column_raises_bad_request_for_unknown_value(repository):
    with pytest.raises(BadRequestError):
        repository._get_group_by_column(repository.model_users, "year")


def test_get_group_by_column_returns_labeled_expressions(repository):
    """
    Each supported ``group_by`` value returns a SQL expression with a
    predictable label that downstream callers depend on.
    """
    day_expr = repository._get_group_by_column(repository.model_users, "day")
    week_expr = repository._get_group_by_column(repository.model_users, "week")
    month_expr = repository._get_group_by_column(repository.model_users, "month")

    assert day_expr.key == "date"
    assert week_expr.key == "week"
    assert month_expr.key == "month"


@pytest.mark.asyncio
async def test_get_dashboard_summary_returns_aggregated_metrics(repository):
    repository._execute_query = AsyncMock(
        side_effect=[
            [{"label": "2026-02-09", "count": 2}],
            [{"label": "2026-02-09", "count": 1}],
            [{"label": "2026-02-09", "count": 100}],
            [{"label": "2026-02-09", "count": 5}],
        ]
    )

    result = await repository.get_dashboard_summary("2026-02-09", "2026-02-09", "day")

    assert result["new_users"][0]["count"] == 2
    assert result["games_opened"][0]["count"] == 1
    assert result["points_earned"][0]["count"] == 100
    assert result["actions_performed"][0]["count"] == 5
    assert repository._execute_query.call_count == 4


@pytest.mark.asyncio
async def test_get_dashboard_summary_logs_returns_per_level_aggregates(repository):
    repository._execute_query = AsyncMock(
        side_effect=[
            [{"label": "2026-02-09", "count": 12}],
            [{"label": "2026-02-09", "count": 7}],
            [{"label": "2026-02-09", "count": 1}],
        ]
    )

    result = await repository.get_dashboard_summary_logs(
        "2026-02-09", "2026-02-09", "day"
    )

    assert result["info"][0]["count"] == 12
    assert result["success"][0]["count"] == 7
    assert result["error"][0]["count"] == 1
    assert repository._execute_query.call_count == 3


def test_process_query_applies_date_filters_and_group_by():
    """
    ``process_query`` is a pure builder around a query object, so it can be
    exercised with a MagicMock to assert the right chained calls happen
    independently of whatever dialect renders the SQL.
    """
    repo = DashboardRepository(session_factory=MagicMock())

    query = MagicMock()
    query.filter.return_value = query
    query.group_by.return_value = query

    repo.process_query(
        query,
        start_date="2026-02-09",
        end_date="2026-02-10",
        group_by_column="col",
    )

    assert query.filter.call_count == 2
    query.group_by.assert_called_once_with("col")


def test_process_query_with_no_filters_returns_query_unchanged():
    repo = DashboardRepository(session_factory=MagicMock())

    query = MagicMock()
    result = repo.process_query(query)

    assert result is query
    query.filter.assert_not_called()
    query.group_by.assert_not_called()
