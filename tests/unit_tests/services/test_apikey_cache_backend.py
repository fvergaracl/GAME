"""
Tests for the API key header cache backends.

- ``InMemoryApiKeyCacheBackend`` is verified directly (TTL behavior is
  driven by ``time.monotonic`` which is patched per-test).
- ``RedisApiKeyCacheBackend`` is exercised against ``fakeredis`` to keep
  the SET / GET / DEL / SCAN semantics honest without needing Redis.
"""

import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.apikey_cache_backend import (
    InMemoryApiKeyCacheBackend,
    RedisApiKeyCacheBackend,
    build_apikey_cache_backend,
)


def _value(prefix: str = "gme_live_xxxxxxxx", active: bool = True):
    return SimpleNamespace(apiKey=prefix, active=active)


@pytest.mark.asyncio
async def test_inmemory_set_then_get_returns_value():
    backend = InMemoryApiKeyCacheBackend()
    await backend.set("hash-1", _value("gme_live_aaaaaaaa"), ttl_seconds=5)

    cached = await backend.get("hash-1")

    assert cached is not None
    assert cached.apiKey == "gme_live_aaaaaaaa"
    assert cached.active is True


@pytest.mark.asyncio
async def test_inmemory_get_returns_none_when_missing():
    backend = InMemoryApiKeyCacheBackend()

    assert await backend.get("never-set") is None


@pytest.mark.asyncio
async def test_inmemory_set_with_non_positive_ttl_is_noop():
    backend = InMemoryApiKeyCacheBackend()

    await backend.set("hash-1", _value(), ttl_seconds=0)
    assert await backend.get("hash-1") is None

    await backend.set("hash-1", _value(), ttl_seconds=-1)
    assert await backend.get("hash-1") is None


@pytest.mark.asyncio
async def test_inmemory_expires_entry_after_ttl():
    backend = InMemoryApiKeyCacheBackend()

    with patch("app.services.apikey_cache_backend.monotonic") as mock_monotonic:
        mock_monotonic.return_value = 1000.0
        await backend.set("hash-1", _value(), ttl_seconds=5)

        mock_monotonic.return_value = 1004.0
        assert (await backend.get("hash-1")) is not None

        # Past the TTL boundary -- expired entries are dropped on read.
        mock_monotonic.return_value = 1006.0
        assert (await backend.get("hash-1")) is None


@pytest.mark.asyncio
async def test_inmemory_delete_removes_only_the_targeted_entry():
    backend = InMemoryApiKeyCacheBackend()
    await backend.set("hash-1", _value("gme_live_aaaaaaaa"), ttl_seconds=5)
    await backend.set("hash-2", _value("gme_live_bbbbbbbb"), ttl_seconds=5)

    await backend.delete("hash-1")

    assert await backend.get("hash-1") is None
    survivor = await backend.get("hash-2")
    assert survivor is not None
    assert survivor.apiKey == "gme_live_bbbbbbbb"


@pytest.mark.asyncio
async def test_inmemory_clear_empties_everything():
    backend = InMemoryApiKeyCacheBackend()
    await backend.set("hash-1", _value(), ttl_seconds=5)
    await backend.set("hash-2", _value(), ttl_seconds=5)

    await backend.clear()

    assert await backend.get("hash-1") is None
    assert await backend.get("hash-2") is None


def test_inmemory_sync_clear_resets_lock_so_new_loop_can_bind():
    backend = InMemoryApiKeyCacheBackend()

    async def _populate():
        await backend.set("hash-1", _value(), ttl_seconds=5)

    # First event loop binds the lock to itself.
    asyncio.run(_populate())
    backend.sync_clear()
    # Without sync_clear's lock reset, the second asyncio.run would raise
    # RuntimeError("asyncio.Lock is bound to a different event loop").
    asyncio.run(_populate())


@pytest.fixture
def fake_redis_client():
    fakeredis = pytest.importorskip("fakeredis")
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.mark.asyncio
async def test_redis_set_persists_value_with_ttl(fake_redis_client):
    backend = RedisApiKeyCacheBackend(fake_redis_client, key_prefix="test:apikey:")

    await backend.set("hash-1", _value("gme_live_aaaaaaaa"), ttl_seconds=30)

    raw = await fake_redis_client.get("test:apikey:hash-1")
    assert raw is not None
    assert "gme_live_aaaaaaaa" in raw
    ttl = await fake_redis_client.ttl("test:apikey:hash-1")
    assert 1 <= ttl <= 30


@pytest.mark.asyncio
async def test_redis_get_roundtrips_simplenamespace(fake_redis_client):
    backend = RedisApiKeyCacheBackend(fake_redis_client, key_prefix="test:apikey:")
    await backend.set("hash-1", _value("gme_live_aaaaaaaa", True), ttl_seconds=30)

    cached = await backend.get("hash-1")

    assert cached is not None
    assert cached.apiKey == "gme_live_aaaaaaaa"
    assert cached.active is True


@pytest.mark.asyncio
async def test_redis_get_returns_none_on_miss(fake_redis_client):
    backend = RedisApiKeyCacheBackend(fake_redis_client, key_prefix="test:apikey:")

    assert await backend.get("never-set") is None


@pytest.mark.asyncio
async def test_redis_set_with_non_positive_ttl_is_noop(fake_redis_client):
    backend = RedisApiKeyCacheBackend(fake_redis_client, key_prefix="test:apikey:")

    await backend.set("hash-1", _value(), ttl_seconds=0)
    assert await fake_redis_client.get("test:apikey:hash-1") is None


@pytest.mark.asyncio
async def test_redis_delete_removes_only_targeted_entry(fake_redis_client):
    backend = RedisApiKeyCacheBackend(fake_redis_client, key_prefix="test:apikey:")
    await backend.set("hash-1", _value("gme_live_aaaaaaaa"), ttl_seconds=30)
    await backend.set("hash-2", _value("gme_live_bbbbbbbb"), ttl_seconds=30)

    await backend.delete("hash-1")

    assert await backend.get("hash-1") is None
    survivor = await backend.get("hash-2")
    assert survivor is not None
    assert survivor.apiKey == "gme_live_bbbbbbbb"


@pytest.mark.asyncio
async def test_redis_clear_only_deletes_prefixed_keys(fake_redis_client):
    backend = RedisApiKeyCacheBackend(fake_redis_client, key_prefix="test:apikey:")
    await backend.set("hash-1", _value(), ttl_seconds=30)
    await backend.set("hash-2", _value(), ttl_seconds=30)
    # An unrelated key that must survive the scan-and-delete.
    await fake_redis_client.set("other:key", "untouched")

    await backend.clear()

    assert await fake_redis_client.get("test:apikey:hash-1") is None
    assert await fake_redis_client.get("test:apikey:hash-2") is None
    assert await fake_redis_client.get("other:key") == "untouched"


def test_build_backend_defaults_to_in_memory():
    backend = build_apikey_cache_backend(
        backend_name="memory",
        redis_url=None,
        redis_key_prefix="game:apikey:",
    )

    assert isinstance(backend, InMemoryApiKeyCacheBackend)


def test_build_backend_falls_back_to_memory_when_redis_url_missing(caplog):
    with caplog.at_level(logging.WARNING, logger="app.services.apikey_cache_backend"):
        backend = build_apikey_cache_backend(
            backend_name="redis",
            redis_url=None,
            redis_key_prefix="game:apikey:",
        )

    assert isinstance(backend, InMemoryApiKeyCacheBackend)
    assert any(
        "APIKEY_CACHE_BACKEND=redis but REDIS_URL is empty" in record.message
        for record in caplog.records
    )


def test_build_backend_returns_redis_backend_when_configured():
    pytest.importorskip("redis")

    with patch(
        "app.services.apikey_cache_backend.build_redis_client_from_url",
        return_value=MagicMock(),
    ) as factory:
        backend = build_apikey_cache_backend(
            backend_name="redis",
            redis_url="redis://localhost:6379/0",
            redis_key_prefix="game:apikey:",
        )

    factory.assert_called_once_with("redis://localhost:6379/0")
    assert isinstance(backend, RedisApiKeyCacheBackend)
