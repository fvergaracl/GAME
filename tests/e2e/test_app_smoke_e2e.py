import pytest
from sqlalchemy import func, select

from app.model.games import Games


@pytest.mark.asyncio
async def test_database_is_clean_on_new_test(e2e_context):
    async with e2e_context.container.db().session() as session:
        result = await session.execute(select(func.count()).select_from(Games))
        assert result.scalar_one() == 0
