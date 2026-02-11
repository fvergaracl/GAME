from unittest.mock import MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.repository.wallet_repository import WalletRepository


def _build_session_factory():
    session = MagicMock()
    context_manager = MagicMock()
    context_manager.__enter__.return_value = session
    context_manager.__exit__.return_value = False
    session_factory = MagicMock(return_value=context_manager)
    return session_factory, session


def _configure_wallet_lookup(session, wallet_id, wallet_obj):
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = wallet_id
    session.execute.return_value = execute_result

    query = MagicMock()
    filtered = MagicMock()
    session.query.return_value = query
    query.filter.return_value = filtered
    filtered.first.return_value = wallet_obj


def test_upsert_points_balance_commits_and_returns_wallet():
    session_factory, session = _build_session_factory()
    repository = WalletRepository(session_factory=session_factory)
    wallet = MagicMock(id="wallet-1")
    _configure_wallet_lookup(session, "wallet-1", wallet)

    result = repository.upsert_points_balance(
        user_id="user-1",
        points_delta=5,
        api_key="api-key-1",
    )

    assert result is wallet
    session.execute.assert_called_once()
    session.commit.assert_called_once()
    session.flush.assert_not_called()


def test_upsert_points_balance_with_external_session_flushes_without_commit():
    session_factory, session = _build_session_factory()
    repository = WalletRepository(session_factory=session_factory)
    wallet = MagicMock(id="wallet-2")
    _configure_wallet_lookup(session, "wallet-2", wallet)

    result = repository.upsert_points_balance(
        user_id="user-2",
        points_delta=7,
        session=session,
        auto_commit=False,
    )

    assert result is wallet
    session.execute.assert_called_once()
    session.flush.assert_called_once()
    session.commit.assert_not_called()


def test_upsert_points_balance_raises_not_found_when_returned_id_has_no_row():
    session_factory, session = _build_session_factory()
    repository = WalletRepository(session_factory=session_factory)
    _configure_wallet_lookup(session, "wallet-missing", None)

    with pytest.raises(NotFoundError):
        repository.upsert_points_balance(
            user_id="user-3",
            points_delta=1,
        )


def test_upsert_points_balance_without_external_session_rejects_auto_commit_false():
    session_factory, _ = _build_session_factory()
    repository = WalletRepository(session_factory=session_factory)

    with pytest.raises(ValueError):
        repository.upsert_points_balance(
            user_id="user-4",
            points_delta=2,
            auto_commit=False,
        )
