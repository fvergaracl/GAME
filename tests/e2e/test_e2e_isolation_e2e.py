import pytest
from sqlalchemy import func, select

from app.model.games import Games


@pytest.mark.asyncio
async def test_e2e_context_starts_with_empty_database(e2e_context):
    async with e2e_context.container.db().session() as session:
        result = await session.execute(select(func.count()).select_from(Games))
        assert result.scalar_one() == 0


@pytest.mark.asyncio
async def test_e2e_context_resets_state_between_tests(e2e_context):
    async with e2e_context.container.db().session() as session:
        game = Games(
            externalGameId="e2e_game_1",
            strategyId="default",
            platform="web",
        )
        session.add(game)
        await session.commit()

    # Within the same test the data persists; between tests the fixture
    # creates a brand-new ControlledDatabase, so isolation is preserved.
    async with e2e_context.container.db().session() as session:
        result = await session.execute(select(func.count()).select_from(Games))
        assert result.scalar_one() == 1
