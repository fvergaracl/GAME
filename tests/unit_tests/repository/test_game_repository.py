"""
Integration tests for ``GameRepository`` against aiosqlite.

Replaces the legacy mocked tests that exercised the sync ``session.query()``
chain. Each test seeds the database via the shared ``db_session`` fixture and
then drives the repository's async API directly.
"""

from uuid import UUID

import pytest

from app.core.exceptions import DuplicatedError, NotFoundError
from app.model.game_params import GamesParams
from app.model.games import Games
from app.model.tasks import Tasks
from app.repository.game_repository import GameRepository
from app.schema.games_schema import PatchGame, PostFindGame


@pytest.fixture
def repository(session_factory):
    return GameRepository(session_factory=session_factory)


async def _seed_game(
    db_session,
    *,
    external_id="ext-1",
    platform="web",
    strategy="default",
    api_key=None,
):
    game = Games(
        externalGameId=external_id,
        platform=platform,
        strategyId=strategy,
        apiKey_used=api_key,
    )
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)
    return game


@pytest.mark.asyncio
async def test_get_game_by_id_returns_game_and_params(repository, db_session):
    game = await _seed_game(db_session)
    db_session.add(GamesParams(gameId=game.id, key="difficulty", value="hard"))
    db_session.add(GamesParams(gameId=game.id, key="lives", value="3"))
    await db_session.commit()

    result = await repository.get_game_by_id(game.id)

    assert str(result.gameId) == str(game.id)
    assert result.externalGameId == "ext-1"
    assert result.platform == "web"
    assert len(result.params) == 2
    keys = {p.key for p in result.params}
    assert keys == {"difficulty", "lives"}


@pytest.mark.asyncio
async def test_get_game_by_id_raises_not_found_when_missing(repository):
    with pytest.raises(NotFoundError):
        await repository.get_game_by_id(UUID("00000000-0000-0000-0000-000000000000"))


@pytest.mark.asyncio
async def test_patch_game_by_id_updates_fields(repository, db_session):
    game = await _seed_game(db_session, external_id="ext-patch")

    updated = await repository.patch_game_by_id(
        game.id,
        PatchGame(platform="mobile"),
    )

    assert updated.platform == "mobile"


@pytest.mark.asyncio
async def test_patch_game_by_id_raises_not_found_when_missing(repository):
    with pytest.raises(NotFoundError):
        await repository.patch_game_by_id(
            UUID("00000000-0000-0000-0000-000000000000"),
            PatchGame(platform="mobile"),
        )


@pytest.mark.asyncio
async def test_patch_game_by_id_raises_duplicated_on_unique_violation(
    repository, db_session
):
    """
    The ``externalGameId`` column has a unique constraint; attempting to
    rename a game to an already-taken external id must surface as
    ``DuplicatedError`` rather than a raw integrity error.
    """
    await _seed_game(db_session, external_id="ext-original")
    other = await _seed_game(db_session, external_id="ext-conflict")

    with pytest.raises(DuplicatedError):
        await repository.patch_game_by_id(
            other.id, PatchGame(externalGameId="ext-original")
        )


@pytest.mark.asyncio
async def test_delete_game_by_id_cascades_params_and_tasks(repository, db_session):
    game = await _seed_game(db_session, external_id="ext-del")
    db_session.add(GamesParams(gameId=game.id, key="k", value="v"))
    task = Tasks(externalTaskId="t-1", gameId=game.id, strategyId="default")
    db_session.add(task)
    await db_session.commit()

    result = await repository.delete_game_by_id(game.id)

    assert result is True
    with pytest.raises(NotFoundError):
        await repository.get_game_by_id(game.id)


@pytest.mark.asyncio
async def test_delete_game_by_id_raises_not_found_when_missing(repository):
    with pytest.raises(NotFoundError):
        await repository.delete_game_by_id(UUID("00000000-0000-0000-0000-000000000000"))


@pytest.mark.asyncio
async def test_get_all_games_returns_paginated_results(repository, db_session):
    for i in range(3):
        await _seed_game(db_session, external_id=f"ext-{i}")

    schema = PostFindGame(
        ordering="externalGameId",
        page=1,
        page_size=10,
    )
    result = await repository.get_all_games(schema, is_admin=True)

    assert result.search_options.total_count == 3
    assert len(result.items) == 3
    assert [item.externalGameId for item in result.items] == [
        "ext-0",
        "ext-1",
        "ext-2",
    ]


@pytest.mark.asyncio
async def test_get_all_games_filters_by_api_key(repository, db_session):
    from app.model.api_key import ApiKey

    api_key_value = "kk-1"
    db_session.add(ApiKey(apiKey=api_key_value, apiKeyHash="h", apiKeyPrefix="p"))
    await db_session.commit()

    await _seed_game(db_session, external_id="ext-with-key", api_key=api_key_value)
    await _seed_game(db_session, external_id="ext-no-key")

    schema = PostFindGame(ordering="externalGameId", page=1, page_size=10)
    result = await repository.get_all_games(schema, api_key=api_key_value)

    assert result.search_options.total_count == 1
    assert result.items[0].externalGameId == "ext-with-key"


@pytest.mark.asyncio
async def test_get_all_games_groups_params_under_each_game(repository, db_session):
    game = await _seed_game(db_session, external_id="ext-group")
    db_session.add(GamesParams(gameId=game.id, key="a", value="1"))
    db_session.add(GamesParams(gameId=game.id, key="b", value="2"))
    await db_session.commit()

    schema = PostFindGame(ordering="externalGameId", page=1, page_size=10)
    result = await repository.get_all_games(schema, is_admin=True)

    assert result.search_options.total_count == 1
    assert len(result.items[0].params) == 2


@pytest.mark.asyncio
async def test_get_all_games_total_count_spans_all_pages(repository, db_session):
    for i in range(5):
        await _seed_game(db_session, external_id=f"ext-{i}")

    schema = PostFindGame(ordering="externalGameId", page=1, page_size=2)
    result = await repository.get_all_games(schema, is_admin=True)

    # total_count reflects every matching game, not just the current page,
    # so the dashboard can render page controls.
    assert result.search_options.total_count == 5
    assert len(result.items) == 2
    assert [item.externalGameId for item in result.items] == [
        "ext-0",
        "ext-1",
    ]


@pytest.mark.asyncio
async def test_get_all_games_page_size_counts_games_not_param_rows(
    repository, db_session
):
    # Regression: pagination used to LIMIT a Games⋈GamesParams join, so a
    # game with several params ate the whole page budget and crowded other
    # games off the page. With page_size=2 and a 3-param game, the old code
    # returned a single game; the page must contain two distinct games.
    game_a = await _seed_game(db_session, external_id="ext-a")
    db_session.add(GamesParams(gameId=game_a.id, key="k1", value="1"))
    db_session.add(GamesParams(gameId=game_a.id, key="k2", value="2"))
    db_session.add(GamesParams(gameId=game_a.id, key="k3", value="3"))
    await _seed_game(db_session, external_id="ext-b")
    await db_session.commit()

    schema = PostFindGame(ordering="externalGameId", page=1, page_size=2)
    result = await repository.get_all_games(schema, is_admin=True)

    assert result.search_options.total_count == 2
    assert [item.externalGameId for item in result.items] == [
        "ext-a",
        "ext-b",
    ]
    params_by_ext = {item.externalGameId: len(item.params) for item in result.items}
    assert params_by_ext == {"ext-a": 3, "ext-b": 0}


@pytest.mark.asyncio
async def test_get_all_games_string_page_size_loads_first_page(repository, db_session):
    # Regression for the "Network Error" on /admin/games (and the strategy
    # assignments view, which calls listGames). Query-string params arrive as
    # strings, and under Pydantic v2 smart-union ``page_size`` stayed "20".
    # On page 1 the repository computed ``(1 - 1) * "20" == ""`` (Python
    # string repetition), so ``.offset("")`` reached SQLAlchemy as
    # ``int("")`` → ValueError → 500 (surfaced as a CORS-less "Network
    # Error" in the browser). ``FindBase`` now coerces numeric page_size
    # strings to int, so the default first page loads.
    for i in range(3):
        await _seed_game(db_session, external_id=f"ext-str-{i}")

    schema = PostFindGame(ordering="externalGameId", page=1, page_size="20")
    assert schema.page_size == 20  # coerced by the FindBase validator

    result = await repository.get_all_games(schema, is_admin=True)

    assert result.search_options.total_count == 3
    assert len(result.items) == 3


@pytest.mark.asyncio
async def test_list_external_ids_maps_ids_to_external(repository, db_session):
    game_a = await _seed_game(db_session, external_id="ext-a")
    game_b = await _seed_game(db_session, external_id="ext-b")

    mapping = await repository.list_external_ids([game_a.id, game_b.id])

    assert mapping == {game_a.id: "ext-a", game_b.id: "ext-b"}


@pytest.mark.asyncio
async def test_list_external_ids_empty_for_no_ids(repository):
    assert await repository.list_external_ids([]) == {}
    assert await repository.list_external_ids([None]) == {}
