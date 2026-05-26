"""
Integration tests for ``GameParamsRepository``.
"""

from uuid import UUID

import pytest

from app.core.exceptions import NotFoundError
from app.model.game_params import GamesParams
from app.model.games import Games
from app.repository.game_params_repository import GameParamsRepository
from app.schema.games_params_schema import UpdateGameParams


@pytest.fixture
def repository(session_factory):
    return GameParamsRepository(session_factory=session_factory)


async def _seed_game_with_param(db_session, *, key="difficulty", value="normal"):
    game = Games(externalGameId="g-1", platform="web", strategyId="default")
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)
    param = GamesParams(gameId=game.id, key=key, value=value)
    db_session.add(param)
    await db_session.commit()
    await db_session.refresh(param)
    return param


@pytest.mark.asyncio
async def test_patch_game_params_by_id_updates_and_returns_refreshed_row(
    repository, db_session
):
    param = await _seed_game_with_param(db_session)

    updated = await repository.patch_game_params_by_id(
        param.id,
        UpdateGameParams(id=param.id, key="difficulty", value="hard"),
    )

    assert updated.id == param.id
    assert updated.value == "hard"


@pytest.mark.asyncio
async def test_patch_game_params_by_id_raises_not_found_when_missing(
    repository,
):
    missing = UUID("00000000-0000-0000-0000-000000000000")

    with pytest.raises(NotFoundError) as exc_info:
        await repository.patch_game_params_by_id(
            missing,
            UpdateGameParams(id=missing, key="difficulty", value="hard"),
        )

    assert "GameParams not found" in str(exc_info.value.detail)
