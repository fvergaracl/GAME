"""
Integration tests for ``UserRepository`` against in-memory aiosqlite.

The repository contains both standard CRUD paths and a Postgres-style
``INSERT ... ON CONFLICT DO UPDATE`` upsert. The conftest ``@compiles`` hook
makes the latter compile correctly under SQLite so we can exercise it for
real instead of mocking the session chain.
"""

import pytest

from app.core.exceptions import NotFoundError
from app.repository.user_repository import UserRepository


@pytest.fixture
def repository(session_factory):
    return UserRepository(session_factory=session_factory)


@pytest.mark.asyncio
async def test_create_user_persists_and_returns_user(repository):
    user = await repository.create_user_by_externalUserId("ext-user-1")

    assert user.id is not None
    assert user.externalUserId == "ext-user-1"
    assert user.oauth_user_id is None


@pytest.mark.asyncio
async def test_create_user_defaults_oauth_id_to_none(repository):
    user = await repository.create_user_by_externalUserId("ext-user-2")

    assert user.oauth_user_id is None


@pytest.mark.asyncio
async def test_create_user_returns_existing_on_duplicate(repository):
    """
    A race-style duplicate externalUserId must return the pre-existing row
    rather than propagating IntegrityError, so the caller sees idempotent
    semantics.
    """
    first = await repository.create_user_by_externalUserId("dup-user")
    second = await repository.create_user_by_externalUserId("dup-user")

    assert first.id == second.id
    assert second.externalUserId == "dup-user"


@pytest.mark.asyncio
async def test_get_or_create_creates_when_missing(repository):
    user = await repository.get_or_create_by_externalUserId(externalUserId="upsert-1")

    assert user.externalUserId == "upsert-1"
    assert user.id is not None


@pytest.mark.asyncio
async def test_get_or_create_returns_existing_user(repository):
    created = await repository.create_user_by_externalUserId("upsert-existing")

    upserted = await repository.get_or_create_by_externalUserId(
        externalUserId="upsert-existing"
    )

    assert upserted.id == created.id


@pytest.mark.asyncio
async def test_get_or_create_updates_oauth_id_when_provided(
    repository, session_factory
):
    """
    When called on an existing row with a new ``oauth_user_id``, the upsert
    must update the linked OAuth identity in place.
    """
    from app.model.oauth_users import OAuthUsers

    async with session_factory() as seed:
        seed.add(
            OAuthUsers(
                provider="google",
                provider_user_id="oauth-link-1",
                email="x@y.z",
            )
        )
        await seed.commit()

    await repository.create_user_by_externalUserId("upsert-oauth")

    upserted = await repository.get_or_create_by_externalUserId(
        externalUserId="upsert-oauth",
        oauth_user_id="oauth-link-1",
    )

    assert upserted.oauth_user_id == "oauth-link-1"


@pytest.mark.asyncio
async def test_get_or_create_requires_session_when_auto_commit_false(repository):
    with pytest.raises(ValueError):
        await repository.get_or_create_by_externalUserId(
            externalUserId="bad", auto_commit=False
        )


@pytest.mark.asyncio
async def test_get_or_create_with_external_session_flushes_only(
    repository, session_factory
):
    """
    When a caller-managed session is supplied with ``auto_commit=False``, the
    repository must flush but not commit - leaving the transaction open for
    the caller to compose with other operations.
    """
    async with session_factory() as session:
        user = await repository.get_or_create_by_externalUserId(
            externalUserId="flush-only",
            session=session,
            auto_commit=False,
        )
        assert user.externalUserId == "flush-only"
        # Roll back so the row never lands.
        await session.rollback()

    # A new transaction must not see the rolled-back row.
    with pytest.raises(NotFoundError):
        await repository.read_by_column("externalUserId", "flush-only")
