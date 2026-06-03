"""
Pluggable cache backends for the API key header lookup.

The in-memory backend preserves the original per-process dict (zero
dependency, fast, but one cache per gunicorn worker -- revocations only
reach the worker that handled the request and other workers serve the
cached value until TTL expires). The Redis backend stores entries in a
single shared keyspace so every worker observes revocations on the next
request.

Selection is driven by ``configs.APIKEY_CACHE_BACKEND`` ("memory" or
"redis") and wired in ``app/core/container.py``.
"""

from __future__ import annotations

import asyncio
import json
import logging
from time import monotonic
from types import SimpleNamespace
from typing import Optional, Protocol, runtime_checkable

from app.services.rate_limit_counter_backend import build_redis_client_from_url

logger = logging.getLogger(__name__)


@runtime_checkable
class ApiKeyCacheBackend(Protocol):
    """Cache the resolved ``(apiKey, active)`` tuple keyed by sha256 hash."""

    async def get(self, cache_key: str) -> Optional[SimpleNamespace]: ...

    async def set(
        self, cache_key: str, value: SimpleNamespace, ttl_seconds: int
    ) -> None: ...

    async def delete(self, cache_key: str) -> None: ...

    async def clear(self) -> None: ...


class InMemoryApiKeyCacheBackend:
    """
    Per-process dict cache with monotonic TTL and lazy eviction.

    The asyncio lock is lazy-bound on first use and reset by ``sync_clear``
    so tests that swap event loops between cases don't trip "attached to a
    different loop". This mirrors the behavior the cache had when it lived
    on ``ApiKeyService`` directly.
    """

    def __init__(self) -> None:
        self._store: dict = {}
        self._lock: Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def get(self, cache_key: str) -> Optional[SimpleNamespace]:
        now = monotonic()
        async with self._get_lock():
            entry = self._store.get(cache_key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= now:
                self._store.pop(cache_key, None)
                return None
            return value

    async def set(
        self, cache_key: str, value: SimpleNamespace, ttl_seconds: int
    ) -> None:
        if ttl_seconds <= 0:
            return
        expires_at = monotonic() + ttl_seconds
        async with self._get_lock():
            self._store[cache_key] = (expires_at, value)

    async def delete(self, cache_key: str) -> None:
        async with self._get_lock():
            self._store.pop(cache_key, None)

    async def clear(self) -> None:
        self.sync_clear()

    def sync_clear(self) -> None:
        # dict.clear() is atomic under the GIL; resetting the lock lets the
        # next async caller bind it to the current event loop.
        self._store.clear()
        self._lock = None


class RedisApiKeyCacheBackend:
    """
    Redis-backed cache shared across workers. Values are stored as compact
    JSON (``{"apiKey": <prefix>, "active": <bool>}``) with TTL set via the
    ``EX`` argument on ``SET`` so Redis handles expiration server-side.
    """

    def __init__(self, client, key_prefix: str = "game:apikey:") -> None:
        self._client = client
        self._key_prefix = key_prefix

    def _build_key(self, cache_key: str) -> str:
        return f"{self._key_prefix}{cache_key}"

    async def get(self, cache_key: str) -> Optional[SimpleNamespace]:
        raw = await self._client.get(self._build_key(cache_key))
        if raw is None:
            return None
        payload = json.loads(raw)
        return SimpleNamespace(
            apiKey=payload.get("apiKey"), active=payload.get("active")
        )

    async def set(
        self, cache_key: str, value: SimpleNamespace, ttl_seconds: int
    ) -> None:
        if ttl_seconds <= 0:
            return
        payload = json.dumps({"apiKey": value.apiKey, "active": value.active})
        await self._client.set(
            self._build_key(cache_key), payload, ex=max(1, int(ttl_seconds))
        )

    async def delete(self, cache_key: str) -> None:
        await self._client.delete(self._build_key(cache_key))

    async def clear(self) -> None:
        # SCAN + DEL is bounded and non-blocking for other clients; only
        # called from admin/maintenance paths, never the request hot path.
        pattern = f"{self._key_prefix}*"
        async for key in self._client.scan_iter(match=pattern, count=500):
            await self._client.delete(key)


def build_apikey_cache_backend(
    backend_name: str,
    redis_url: Optional[str],
    redis_key_prefix: str,
) -> ApiKeyCacheBackend:
    """
    Select the configured backend. Falls back to the in-memory backend with
    a warning when Redis is requested but ``REDIS_URL`` is missing -- so a
    misconfigured deploy still authenticates (just with the per-process
    consistency caveat) instead of failing requests outright.
    """
    normalized = (backend_name or "memory").strip().lower()
    if normalized == "redis":
        if not redis_url:
            logger.warning(
                "APIKEY_CACHE_BACKEND=redis but REDIS_URL is empty; "
                "falling back to the in-process API key cache."
            )
            return InMemoryApiKeyCacheBackend()
        client = build_redis_client_from_url(redis_url)
        return RedisApiKeyCacheBackend(client, key_prefix=redis_key_prefix)
    return InMemoryApiKeyCacheBackend()
