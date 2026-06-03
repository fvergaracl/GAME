"""
Integration tests for the thin repositories that mostly just inherit
``BaseRepository`` plus a small extension method. They are bundled here
because none of them carries enough surface area to warrant its own file.
"""

import pytest

from app.model.abuse_limit_counter import AbuseLimitCounter
from app.model.api_key import ApiKey
from app.model.api_requests import ApiRequests
from app.model.kpi_metrics import KpiMetrics
from app.model.logs import Logs
from app.model.oauth_users import OAuthUsers
from app.model.uptime_logs import UptimeLogs
from app.model.user_interactions import UserInteractions
from app.repository.abuse_limit_counter_repository import AbuseLimitCounterRepository
from app.repository.api_requests_repository import ApiRequestsRepository
from app.repository.apikey_repository import ApiKeyRepository
from app.repository.kpi_metrics_repository import KpiMetricsRepository
from app.repository.logs_repository import LogsRepository
from app.repository.oauth_users_repository import OAuthUsersRepository
from app.repository.uptime_logs_repository import UptimeLogsRepository
from app.repository.user_game_config_repository import UserGameConfigRepository
from app.repository.user_interactions_repository import UserInteractionsRepository


def test_light_repositories_set_expected_default_models(session_factory):
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


@pytest.mark.asyncio
async def test_apikey_repository_read_all_returns_persisted_keys(
    session_factory, db_session
):
    repository = ApiKeyRepository(session_factory=session_factory)
    db_session.add(
        ApiKey(
            apiKey="ak-a",
            apiKeyHash="h-a",
            client="c",
            createdBy="user-1",
        )
    )
    db_session.add(
        ApiKey(
            apiKey="ak-b",
            apiKeyHash="h-b",
            client="c",
            createdBy="user-1",
        )
    )
    await db_session.commit()

    result = await repository.read_all(page=1, page_size=10)

    assert {k.apiKey for k in result} == {"ak-a", "ak-b"}


@pytest.mark.asyncio
async def test_apikey_repository_read_all_caps_page_size_to_100(
    session_factory, db_session
):
    """
    Asking for a page size above 100 must be clamped to 100 to bound
    response payloads.
    """
    repository = ApiKeyRepository(session_factory=session_factory)
    for i in range(120):
        db_session.add(
            ApiKey(
                apiKey=f"ak-{i:03d}",
                apiKeyHash=f"h-{i:03d}",
                client="c",
                createdBy="user-1",
            )
        )
    await db_session.commit()

    result = await repository.read_all(page=1, page_size=1000)

    assert len(result) == 100


@pytest.mark.asyncio
async def test_oauth_users_repository_get_user_by_sub(session_factory, db_session):
    repository = OAuthUsersRepository(session_factory=session_factory)
    db_session.add(
        OAuthUsers(
            provider="google",
            provider_user_id="sub-1",
            status="active",
        )
    )
    await db_session.commit()

    found = await repository.get_user_by_sub("sub-1")
    missing = await repository.get_user_by_sub("not-here")

    assert found is not None
    assert found.provider_user_id == "sub-1"
    assert missing is None


@pytest.mark.asyncio
async def test_user_game_config_repository_get_all_users_by_game_id(
    session_factory, db_session
):
    """
    The ``get_all_users_by_gameId`` shortcut returns every configuration row
    bound to the requested game, leaving filtering of other games to the
    caller.
    """
    from app.model.games import Games
    from app.model.user_game_config import UserGameConfig
    from app.model.users import Users

    repository = UserGameConfigRepository(session_factory=session_factory)
    user_a = Users(externalUserId="ext-ugc-a")
    user_b = Users(externalUserId="ext-ugc-b")
    game_target = Games(externalGameId="g-target", platform="web", strategyId="d")
    game_other = Games(externalGameId="g-other", platform="web", strategyId="d")
    db_session.add_all([user_a, user_b, game_target, game_other])
    await db_session.commit()

    db_session.add(
        UserGameConfig(
            userId=user_a.id,
            gameId=game_target.id,
            experimentGroup="A",
            configData={},
        )
    )
    db_session.add(
        UserGameConfig(
            userId=user_b.id,
            gameId=game_target.id,
            experimentGroup="B",
            configData={},
        )
    )
    db_session.add(
        UserGameConfig(
            userId=user_a.id,
            gameId=game_other.id,
            experimentGroup="A",
            configData={},
        )
    )
    await db_session.commit()

    rows = await repository.get_all_users_by_gameId(game_target.id)

    assert len(rows) == 2
    assert {r.experimentGroup for r in rows} == {"A", "B"}
