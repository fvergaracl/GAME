"""
Integration tests for ``WalletRepository`` against aiosqlite.

Exercises the Postgres-dialect upsert (``INSERT ... ON CONFLICT DO UPDATE``)
which is rendered on SQLite via the conftest ``@compiles`` hook.
"""

import pytest

from app.core.exceptions import NotFoundError
from app.model.users import Users
from app.repository.wallet_repository import WalletRepository


@pytest.fixture
def repository(session_factory):
    return WalletRepository(session_factory=session_factory)


async def _seed_user(db_session, external_id="ext-w-1"):
    user = Users(externalUserId=external_id)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_upsert_creates_wallet_when_missing(repository, db_session):
    user = await _seed_user(db_session)

    wallet = await repository.upsert_points_balance(user_id=user.id, points_delta=5)

    assert wallet.id is not None
    assert wallet.pointsBalance == 5
    assert str(wallet.userId) == str(user.id)


@pytest.mark.asyncio
async def test_upsert_increments_existing_wallet(repository, db_session):
    user = await _seed_user(db_session, "ext-w-incr")

    await repository.upsert_points_balance(user_id=user.id, points_delta=3)
    second = await repository.upsert_points_balance(user_id=user.id, points_delta=7)

    assert second.pointsBalance == 10


@pytest.mark.asyncio
async def test_upsert_updates_api_key_when_provided(repository, db_session):
    from app.model.api_key import ApiKey

    user = await _seed_user(db_session, "ext-w-apik")
    db_session.add(ApiKey(apiKey="ak-1", apiKeyHash="h", apiKeyPrefix="p"))
    await db_session.commit()

    await repository.upsert_points_balance(user_id=user.id, points_delta=1)
    second = await repository.upsert_points_balance(
        user_id=user.id, points_delta=1, api_key="ak-1"
    )

    assert second.apiKey_used == "ak-1"


@pytest.mark.asyncio
async def test_upsert_rejects_auto_commit_false_without_session(repository):
    with pytest.raises(ValueError):
        await repository.upsert_points_balance(
            user_id="00000000-0000-0000-0000-000000000000",
            points_delta=1,
            auto_commit=False,
        )


@pytest.mark.asyncio
async def test_upsert_with_external_session_flushes_only(
    repository, session_factory, db_session
):
    user = await _seed_user(db_session, "ext-w-flush")

    async with session_factory() as session:
        wallet = await repository.upsert_points_balance(
            user_id=user.id,
            points_delta=2,
            session=session,
            auto_commit=False,
        )
        assert wallet.pointsBalance == 2
        await session.rollback()

    # A subsequent insert from scratch must see the balance reset to delta
    # because the previous transaction rolled back.
    fresh = await repository.upsert_points_balance(user_id=user.id, points_delta=4)
    assert fresh.pointsBalance == 4
