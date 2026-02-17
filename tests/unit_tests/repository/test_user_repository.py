from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import NotFoundError
from app.repository.user_repository import UserRepository


def build_repository():
    session = MagicMock()
    context_manager = MagicMock()
    context_manager.__enter__.return_value = session
    context_manager.__exit__.return_value = False
    session_factory = MagicMock(return_value=context_manager)
    repository = UserRepository(session_factory=session_factory)
    return repository, session


def _configure_user_lookup(session, user_id, user_obj):
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = user_id
    session.execute.return_value = execute_result

    query = MagicMock()
    filtered = MagicMock()
    session.query.return_value = query
    query.filter.return_value = filtered
    filtered.first.return_value = user_obj


@pytest.mark.asyncio
async def test_create_user_by_external_user_id_persists_and_returns_user():
    repository, session = build_repository()

    result = await repository.create_user_by_externalUserId("external-user-1", "oauth-user-1")

    session.add.assert_called_once()
    added_user = session.add.call_args.args[0]
    assert added_user.externalUserId == "external-user-1"
    assert added_user.oauth_user_id == "oauth-user-1"
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(added_user)
    assert result is added_user


@pytest.mark.asyncio
async def test_create_user_by_external_user_id_defaults_oauth_to_none():
    repository, session = build_repository()

    result = await repository.create_user_by_externalUserId("external-user-2")

    session.add.assert_called_once()
    added_user = session.add.call_args.args[0]
    assert added_user.externalUserId == "external-user-2"
    assert added_user.oauth_user_id is None
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(added_user)
    assert result is added_user


@pytest.mark.asyncio
async def test_create_user_by_external_user_id_returns_existing_on_integrity_race():
    repository, session = build_repository()
    existing_user = MagicMock()
    session.commit.side_effect = IntegrityError("insert into users", {}, Exception("duplicate key"))
    session.query.return_value.filter_by.return_value.first.return_value = existing_user

    result = await repository.create_user_by_externalUserId("external-user-3")

    session.rollback.assert_called_once()
    session.query.assert_called_once_with(repository.model)
    session.query.return_value.filter_by.assert_called_once_with(
        externalUserId="external-user-3"
    )
    assert result is existing_user
    session.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_create_user_by_external_user_id_raises_when_integrity_race_has_no_existing():
    repository, session = build_repository()
    session.commit.side_effect = IntegrityError("insert into users", {}, Exception("duplicate key"))
    session.query.return_value.filter_by.return_value.first.return_value = None

    with pytest.raises(IntegrityError):
        await repository.create_user_by_externalUserId("external-user-4")

    session.rollback.assert_called_once()


def test_get_or_create_by_external_user_id_commits_and_returns_user():
    repository, session = build_repository()
    user = MagicMock(id="user-1")
    _configure_user_lookup(session, "user-1", user)

    result = repository.get_or_create_by_externalUserId(
        externalUserId="external-user-5",
        oauth_user_id="oauth-user-5",
    )

    assert result is user
    session.execute.assert_called_once()
    session.commit.assert_called_once()
    session.flush.assert_not_called()


def test_get_or_create_by_external_user_id_with_external_session_flushes():
    repository, session = build_repository()
    user = MagicMock(id="user-2")
    _configure_user_lookup(session, "user-2", user)

    result = repository.get_or_create_by_externalUserId(
        externalUserId="external-user-6",
        session=session,
        auto_commit=False,
    )

    assert result is user
    session.execute.assert_called_once()
    session.flush.assert_called_once()
    session.commit.assert_not_called()


def test_get_or_create_by_external_user_id_raises_when_user_not_found_after_upsert():
    repository, session = build_repository()
    _configure_user_lookup(session, "user-missing", None)

    with pytest.raises(NotFoundError):
        repository.get_or_create_by_externalUserId(
            externalUserId="external-user-7",
            session=session,
        )


def test_get_or_create_by_external_user_id_requires_external_session_when_no_auto_commit():
    repository, _ = build_repository()

    with pytest.raises(ValueError):
        repository.get_or_create_by_externalUserId(
            externalUserId="external-user-8",
            auto_commit=False,
        )
