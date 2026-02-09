from unittest.mock import MagicMock

import pytest

from app.repository.user_repository import UserRepository


def build_repository():
    session = MagicMock()
    context_manager = MagicMock()
    context_manager.__enter__.return_value = session
    context_manager.__exit__.return_value = False
    session_factory = MagicMock(return_value=context_manager)
    repository = UserRepository(session_factory=session_factory)
    return repository, session


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
