"""
Integration tests for ``UserGameConfigRepository``. Covers the three async
methods that the ``UserGameConfigService`` invokes
(``get_by_user_and_game`` / ``create_or_update`` / ``delete``) — these were
missing from the repository, even though the service awaited them, so they
existed only as ``AsyncMock`` shapes in service-layer tests.
"""

from uuid import uuid4

import pytest

from app.model.games import Games
from app.model.user_game_config import UserGameConfig
from app.model.users import Users
from app.repository.user_game_config_repository import UserGameConfigRepository


@pytest.fixture
def repository(session_factory):
    return UserGameConfigRepository(session_factory=session_factory)


async def _seed_user_and_game(db_session, ext_user="ext-cfg-1", ext_game="g-cfg-1"):
    user = Users(externalUserId=ext_user)
    game = Games(externalGameId=ext_game, platform="web", strategyId="d")
    db_session.add_all([user, game])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(game)
    return user, game


@pytest.mark.asyncio
async def test_get_by_user_and_game_returns_none_when_missing(repository):
    result = await repository.get_by_user_and_game(uuid4(), uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_create_or_update_inserts_when_pair_is_new(
    repository, db_session
):
    user, game = await _seed_user_and_game(db_session)

    created = await repository.create_or_update(
        user.id, game.id, "A", {"k": "v"}
    )

    assert created.id is not None
    assert created.experimentGroup == "A"
    assert created.configData == {"k": "v"}


@pytest.mark.asyncio
async def test_create_or_update_updates_existing_pair_in_place(
    repository, db_session
):
    user, game = await _seed_user_and_game(db_session, "ext-up", "g-up")

    first = await repository.create_or_update(user.id, game.id, "A", {"v": 1})
    second = await repository.create_or_update(
        user.id, game.id, "B", {"v": 2}
    )

    assert first.id == second.id
    assert second.experimentGroup == "B"
    assert second.configData == {"v": 2}


@pytest.mark.asyncio
async def test_get_by_user_and_game_returns_persisted_row(
    repository, db_session
):
    user, game = await _seed_user_and_game(db_session, "ext-get", "g-get")
    await repository.create_or_update(user.id, game.id, "C", {"z": 9})

    fetched = await repository.get_by_user_and_game(user.id, game.id)

    assert fetched is not None
    assert fetched.experimentGroup == "C"
    assert fetched.configData == {"z": 9}


@pytest.mark.asyncio
async def test_delete_returns_true_and_removes_row_when_present(
    repository, db_session
):
    user, game = await _seed_user_and_game(db_session, "ext-del", "g-del")
    await repository.create_or_update(user.id, game.id, "A", None)

    deleted = await repository.delete(user.id, game.id)

    assert deleted is True
    assert await repository.get_by_user_and_game(user.id, game.id) is None


@pytest.mark.asyncio
async def test_delete_returns_false_when_row_missing(repository):
    deleted = await repository.delete(uuid4(), uuid4())
    assert deleted is False


@pytest.mark.asyncio
async def test_get_all_users_by_gameid_returns_configs_for_a_game(
    repository, db_session
):
    user_a, game = await _seed_user_and_game(db_session, "ext-all-a", "g-all")
    user_b = Users(externalUserId="ext-all-b")
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_b)

    await repository.create_or_update(user_a.id, game.id, "A", None)
    await repository.create_or_update(user_b.id, game.id, "B", None)

    rows = await repository.get_all_users_by_gameId(game.id)

    assert len(rows) == 2
    assert {r.experimentGroup for r in rows} == {"A", "B"}
    assert all(isinstance(r, UserGameConfig) for r in rows)
