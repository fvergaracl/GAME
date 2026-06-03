"""
Tests for the rate-limit counter backends.

- ``DatabaseRateLimitCounterBackend`` is verified as a thin adapter over the
  existing repository (the repository itself is covered by its own
  integration tests against aiosqlite).
- ``RedisRateLimitCounterBackend`` is verified against ``fakeredis`` so the
  INCR + EXPIRE semantics are exercised without standing up Redis.
"""

import asyncio
import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repository.abuse_limit_counter_repository import AbuseLimitCounterRepository
from app.services.rate_limit_counter_backend import (DatabaseRateLimitCounterBackend,
                                                     RedisRateLimitCounterBackend,
                                                     build_rate_limit_counter_backend)


def _window():
    return datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_database_backend_delegates_to_repository_and_ignores_ttl():
    repository = MagicMock(spec=AbuseLimitCounterRepository)
    repository.increment_and_get = AsyncMock(return_value=7)
    backend = DatabaseRateLimitCounterBackend(repository)

    value = await backend.increment_and_get(
        scope_type="api_key",
        scope_value="k-1",
        window_name="task_mutation_short_60s",
        window_start=_window(),
        ttl_seconds=120,
    )

    assert value == 7
    repository.increment_and_get.assert_awaited_once_with(
        scope_type="api_key",
        scope_value="k-1",
        window_name="task_mutation_short_60s",
        window_start=_window(),
    )


@pytest.fixture
def fake_redis_client():
    fakeredis = pytest.importorskip("fakeredis")
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.mark.asyncio
async def test_redis_backend_increments_and_sets_ttl_on_first_write(fake_redis_client):
    backend = RedisRateLimitCounterBackend(fake_redis_client, key_prefix="test:rl:")

    value = await backend.increment_and_get(
        scope_type="api_key",
        scope_value="k-1",
        window_name="task_mutation_short_60s",
        window_start=_window(),
        ttl_seconds=65,
    )

    assert value == 1
    key = backend._build_key("api_key", "k-1", "task_mutation_short_60s", _window())
    assert key.startswith("test:rl:task_mutation_short_60s:api_key:k-1:")
    ttl = await fake_redis_client.ttl(key)
    # TTL was planted via SET NX EX and survives subsequent INCRs unchanged.
    assert 1 <= ttl <= 65


@pytest.mark.asyncio
async def test_redis_backend_does_not_reset_ttl_on_subsequent_writes(
    fake_redis_client,
):
    backend = RedisRateLimitCounterBackend(fake_redis_client, key_prefix="test:rl:")

    await backend.increment_and_get(
        scope_type="api_key",
        scope_value="k-1",
        window_name="task_mutation_short_60s",
        window_start=_window(),
        ttl_seconds=65,
    )
    key = backend._build_key("api_key", "k-1", "task_mutation_short_60s", _window())
    await fake_redis_client.expire(key, 30)

    value = await backend.increment_and_get(
        scope_type="api_key",
        scope_value="k-1",
        window_name="task_mutation_short_60s",
        window_start=_window(),
        ttl_seconds=65,
    )

    assert value == 2
    ttl = await fake_redis_client.ttl(key)
    # The shortened TTL is preserved because SET NX is a no-op on existing
    # keys; this proves the backend implements a fixed window, not sliding.
    assert ttl <= 30


@pytest.mark.asyncio
async def test_redis_backend_increments_are_stable_under_concurrency(
    fake_redis_client,
):
    backend = RedisRateLimitCounterBackend(fake_redis_client, key_prefix="test:rl:")

    async def _run_once():
        await backend.increment_and_get(
            scope_type="api_key",
            scope_value="k-1",
            window_name="task_mutation_short_60s",
            window_start=_window(),
            ttl_seconds=65,
        )

    await asyncio.gather(*[_run_once() for _ in range(25)])

    key = backend._build_key("api_key", "k-1", "task_mutation_short_60s", _window())
    final = int(await fake_redis_client.get(key))
    assert final == 25


@pytest.mark.asyncio
async def test_redis_backend_isolates_scopes_and_buckets(fake_redis_client):
    backend = RedisRateLimitCounterBackend(fake_redis_client, key_prefix="test:rl:")

    a = await backend.increment_and_get(
        scope_type="api_key",
        scope_value="k-A",
        window_name="task_mutation_short_60s",
        window_start=_window(),
        ttl_seconds=65,
    )
    b = await backend.increment_and_get(
        scope_type="api_key",
        scope_value="k-B",
        window_name="task_mutation_short_60s",
        window_start=_window(),
        ttl_seconds=65,
    )
    next_bucket = datetime(2026, 2, 10, 12, 1, 0, tzinfo=timezone.utc)
    c = await backend.increment_and_get(
        scope_type="api_key",
        scope_value="k-A",
        window_name="task_mutation_short_60s",
        window_start=next_bucket,
        ttl_seconds=65,
    )

    assert a == 1
    assert b == 1
    assert c == 1


def test_build_backend_returns_database_backend_by_default():
    repository = MagicMock(spec=AbuseLimitCounterRepository)

    backend = build_rate_limit_counter_backend(
        repository=repository,
        backend_name="database",
        redis_url=None,
        redis_key_prefix="game:rl:",
    )

    assert isinstance(backend, DatabaseRateLimitCounterBackend)


def test_build_backend_falls_back_to_database_when_redis_url_missing(caplog):
    repository = MagicMock(spec=AbuseLimitCounterRepository)

    with caplog.at_level(
        logging.WARNING, logger="app.services.rate_limit_counter_backend"
    ):
        backend = build_rate_limit_counter_backend(
            repository=repository,
            backend_name="redis",
            redis_url=None,
            redis_key_prefix="game:rl:",
        )

    assert isinstance(backend, DatabaseRateLimitCounterBackend)
    assert any(
        "ABUSE_PREVENTION_BACKEND=redis but REDIS_URL is empty" in record.message
        for record in caplog.records
    )


def test_build_backend_returns_redis_backend_when_configured():
    pytest.importorskip("redis")
    repository = MagicMock(spec=AbuseLimitCounterRepository)

    backend = build_rate_limit_counter_backend(
        repository=repository,
        backend_name="redis",
        redis_url="redis://localhost:6379/0",
        redis_key_prefix="game:rl:",
    )

    assert isinstance(backend, RedisRateLimitCounterBackend)
