"""
Integration tests for ``AbuseLimitCounterRepository`` against aiosqlite.

The repository implements an upsert-with-retry that protects per-scope
counters under concurrent writes; these tests verify the update / insert
branches behave correctly end-to-end against a real session.
"""

from datetime import datetime, timezone

import pytest

from app.model.abuse_limit_counter import AbuseLimitCounter
from app.repository.abuse_limit_counter_repository import \
    AbuseLimitCounterRepository


@pytest.fixture
def repository(session_factory):
    return AbuseLimitCounterRepository(session_factory=session_factory)


def _window():
    return datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)


def test_repository_defaults_to_abuse_limit_counter_model(session_factory):
    repository = AbuseLimitCounterRepository(session_factory=session_factory)

    assert repository.model is AbuseLimitCounter


@pytest.mark.asyncio
async def test_increment_inserts_when_bucket_missing(repository):
    value = await repository.increment_and_get(
        scope_type="api_key",
        scope_value="k-1",
        window_name="task_mutation_short_60s",
        window_start=_window(),
    )

    assert value == 1


@pytest.mark.asyncio
async def test_increment_updates_existing_bucket(repository):
    window = _window()
    for _ in range(3):
        await repository.increment_and_get(
            scope_type="api_key",
            scope_value="k-2",
            window_name="task_mutation_short_60s",
            window_start=window,
        )

    # Fourth increment must hit the update branch and return 4.
    value = await repository.increment_and_get(
        scope_type="api_key",
        scope_value="k-2",
        window_name="task_mutation_short_60s",
        window_start=window,
    )

    assert value == 4


@pytest.mark.asyncio
async def test_increment_treats_window_start_without_tz_as_utc(repository):
    """
    Naive ``window_start`` values are coerced to UTC so the
    (scope, window) unique key stays stable across callers that forget to
    attach a timezone.
    """
    naive_window = datetime(2026, 2, 10, 12, 0, 0)
    aware_window = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)

    first = await repository.increment_and_get(
        scope_type="ip",
        scope_value="203.0.113.10",
        window_name="task_mutation_short_60s",
        window_start=naive_window,
    )
    second = await repository.increment_and_get(
        scope_type="ip",
        scope_value="203.0.113.10",
        window_name="task_mutation_short_60s",
        window_start=aware_window,
    )

    assert first == 1
    assert second == 2


@pytest.mark.asyncio
async def test_increment_distinct_scopes_keep_independent_counters(repository):
    window = _window()

    a = await repository.increment_and_get(
        scope_type="external_user",
        scope_value="user-A",
        window_name="task_mutation_short_60s",
        window_start=window,
    )
    b = await repository.increment_and_get(
        scope_type="external_user",
        scope_value="user-B",
        window_name="task_mutation_short_60s",
        window_start=window,
    )

    assert a == 1
    assert b == 1
