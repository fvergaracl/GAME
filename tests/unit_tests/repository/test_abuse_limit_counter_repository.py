from datetime import datetime, timezone
from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError

from app.model.abuse_limit_counter import AbuseLimitCounter
from app.repository.abuse_limit_counter_repository import AbuseLimitCounterRepository


def _build_session_factory():
    session = MagicMock()
    context_manager = MagicMock()
    context_manager.__enter__.return_value = session
    context_manager.__exit__.return_value = False
    session_factory = MagicMock(return_value=context_manager)
    return session_factory, session


def test_repository_uses_abuse_limit_counter_model_by_default():
    session_factory, _ = _build_session_factory()
    repository = AbuseLimitCounterRepository(session_factory=session_factory)

    assert repository.model is AbuseLimitCounter


def test_increment_and_get_updates_existing_counter_bucket():
    session_factory, session = _build_session_factory()
    repository = AbuseLimitCounterRepository(session_factory=session_factory)

    query_update = MagicMock()
    query_update.filter.return_value.update.return_value = 1
    query_read = MagicMock()
    query_read.filter.return_value.scalar.return_value = 7
    session.query.side_effect = [query_update, query_read]

    result = repository.increment_and_get(
        scope_type="api_key",
        scope_value="k-1",
        window_name="task_mutation_short_60s",
        window_start=datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert result == 7
    session.add.assert_not_called()
    assert session.commit.call_count == 1


def test_increment_and_get_inserts_when_bucket_does_not_exist():
    session_factory, session = _build_session_factory()
    repository = AbuseLimitCounterRepository(session_factory=session_factory)

    query_update = MagicMock()
    query_update.filter.return_value.update.return_value = 0
    session.query.return_value = query_update

    result = repository.increment_and_get(
        scope_type="ip",
        scope_value="203.0.113.10",
        window_name="task_mutation_short_60s",
        window_start=datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert result == 1
    session.add.assert_called_once()
    assert session.commit.call_count == 1


def test_increment_and_get_retries_update_on_insert_integrity_error():
    session_factory, session = _build_session_factory()
    repository = AbuseLimitCounterRepository(session_factory=session_factory)

    query_update_initial = MagicMock()
    query_update_initial.filter.return_value.update.return_value = 0
    query_update_retry = MagicMock()
    query_update_retry.filter.return_value.update.return_value = 1
    query_read = MagicMock()
    query_read.filter.return_value.scalar.return_value = 2
    session.query.side_effect = [query_update_initial, query_update_retry, query_read]
    session.commit.side_effect = [
        IntegrityError("insert", {}, Exception("duplicate key")),
        None,
    ]

    result = repository.increment_and_get(
        scope_type="external_user",
        scope_value="user_1",
        window_name="task_mutation_short_60s",
        window_start=datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert result == 2
    session.add.assert_called_once()
    session.rollback.assert_called_once()
    assert session.commit.call_count == 2
