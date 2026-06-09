"""
Pluggable counter backends used by ``AbusePreventionService``.

The DB-backed backend writes to ``abuse_limit_counter`` (preserves the
historical behavior and keeps existing migrations relevant). The Redis-backed
backend uses ``INCR`` + ``SET NX EX`` which is atomic, ~50 us per request,
and naturally distributed across API instances -- the cost an ``UPDATE`` on
a hot row in Postgres does not pay.

Selection is driven by ``configs.ABUSE_PREVENTION_BACKEND`` and wired in
``app/core/container.py``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional, Protocol, runtime_checkable

from app.repository.abuse_limit_counter_repository import AbuseLimitCounterRepository

logger = logging.getLogger(__name__)


@runtime_checkable
class RateLimitCounterBackend(Protocol):
    """Increment a per-bucket counter and return its new value."""

    async def increment_and_get(
        self,
        scope_type: str,
        scope_value: str,
        window_name: str,
        window_start: datetime,
        ttl_seconds: int,
    ) -> int:
        """Increment the bucket's counter and return its new value."""
        ...


class DatabaseRateLimitCounterBackend:
    """
    Backend that persists counters in ``abuse_limit_counter``.

    ``ttl_seconds`` is unused because the row's bucket key already encodes
    window boundaries; expired rows can be reaped offline (a future periodic
    job, not the request path).
    """

    def __init__(self, repository: AbuseLimitCounterRepository) -> None:
        self._repository = repository

    async def increment_and_get(
        self,
        scope_type: str,
        scope_value: str,
        window_name: str,
        window_start: datetime,
        ttl_seconds: int,
    ) -> int:
        """
        Increment a DB-backed rate-limit counter and return its value.

        ``ttl_seconds`` is ignored: the bucket's ``window_start`` already
        encodes window boundaries, so expiry is handled offline.

        Args:
            scope_type (str): Dimension being limited.
            scope_value (str): Concrete value within ``scope_type``.
            window_name (str): Name of the time window/bucket.
            window_start (datetime): Start of the bucket window.
            ttl_seconds (int): Ignored by this backend.

        Returns:
            int: The counter value after the increment.
        """
        del ttl_seconds  # bucket key carries window semantics for the DB backend
        return await self._repository.increment_and_get(
            scope_type=scope_type,
            scope_value=scope_value,
            window_name=window_name,
            window_start=window_start,
        )


class RedisRateLimitCounterBackend:
    """
    Backend that uses Redis ``INCR`` + ``SET NX EX`` for per-bucket counters.

    Each bucket maps to one key with a TTL slightly longer than the window.
    ``SET key 0 EX ttl NX`` plants a zeroed counter with a TTL atomically on
    the first request of a bucket; subsequent ``INCR`` calls just bump it.
    The pipeline below batches both commands into a single round-trip and
    runs under ``MULTI/EXEC`` so other clients cannot observe a key without
    a TTL.
    """

    def __init__(self, client, key_prefix: str = "game:rl:") -> None:
        self._client = client
        self._key_prefix = key_prefix

    @staticmethod
    def _bucket_epoch(window_start: datetime) -> int:
        """
        Return the UTC unix timestamp of a bucket's window start.

        Args:
            window_start (datetime): Start of the bucket window (naive treated
                as UTC).

        Returns:
            int: Unix epoch seconds, used to make the Redis key unique per
            window.
        """
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=timezone.utc)
        else:
            window_start = window_start.astimezone(timezone.utc)
        return int(window_start.timestamp())

    def _build_key(
        self,
        scope_type: str,
        scope_value: str,
        window_name: str,
        window_start: datetime,
    ) -> str:
        """
        Build the Redis key uniquely identifying a rate-limit bucket.

        Args:
            scope_type (str): Dimension being limited.
            scope_value (str): Concrete value within ``scope_type``.
            window_name (str): Name of the time window.
            window_start (datetime): Start of the bucket window.

        Returns:
            str: The fully-qualified, prefixed Redis key.
        """
        return (
            f"{self._key_prefix}{window_name}:{scope_type}:"
            f"{scope_value}:{self._bucket_epoch(window_start)}"
        )

    async def increment_and_get(
        self,
        scope_type: str,
        scope_value: str,
        window_name: str,
        window_start: datetime,
        ttl_seconds: int,
    ) -> int:
        """
        Increment a Redis-backed rate-limit counter and return its value.

        Uses a single ``MULTI/EXEC`` pipeline of ``SET key 0 EX ttl NX`` (plant
        a TTL'd zero on the first hit) followed by ``INCR`` so a key is never
        visible without a TTL.

        Args:
            scope_type (str): Dimension being limited.
            scope_value (str): Concrete value within ``scope_type``.
            window_name (str): Name of the time window/bucket.
            window_start (datetime): Start of the bucket window.
            ttl_seconds (int): Key TTL (clamped to ≥ 1 second).

        Returns:
            int: The counter value after the increment.
        """
        key = self._build_key(scope_type, scope_value, window_name, window_start)
        ttl = max(1, int(ttl_seconds))

        pipe = self._client.pipeline(transaction=True)
        pipe.set(key, 0, ex=ttl, nx=True)
        pipe.incr(key)
        results = await pipe.execute()
        return int(results[1])


def build_redis_client_from_url(url: str) -> Any:
    """
    Build an async Redis client from a connection URL.

    Imported lazily so the ``redis`` package is only required when the Redis
    backend is actually selected -- callers running the DB backend never pay
    the dependency cost.
    """
    try:
        from redis import asyncio as redis_asyncio
    except ImportError as exc:  # pragma: no cover - import guard
        raise RuntimeError(
            "ABUSE_PREVENTION_BACKEND=redis requires the 'redis' package. "
            "Install with `poetry add redis@^8.0` or set "
            "ABUSE_PREVENTION_BACKEND=database to keep the DB-backed limiter."
        ) from exc

    return redis_asyncio.from_url(url, decode_responses=True)


def build_rate_limit_counter_backend(
    repository: AbuseLimitCounterRepository,
    backend_name: str,
    redis_url: Optional[str],
    redis_key_prefix: str,
) -> RateLimitCounterBackend:
    """
    Select the configured backend. Falls back to the DB backend with a
    warning when Redis is requested but ``REDIS_URL`` is missing -- so a
    misconfigured deploy still rate-limits (just slower) instead of opening
    the floodgates.
    """
    normalized = (backend_name or "database").strip().lower()
    if normalized == "redis":
        if not redis_url:
            logger.warning(
                "ABUSE_PREVENTION_BACKEND=redis but REDIS_URL is empty; "
                "falling back to the database-backed counter."
            )
            return DatabaseRateLimitCounterBackend(repository)
        client = build_redis_client_from_url(redis_url)
        return RedisRateLimitCounterBackend(client, key_prefix=redis_key_prefix)
    return DatabaseRateLimitCounterBackend(repository)
