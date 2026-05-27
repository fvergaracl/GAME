import asyncio
import threading
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.core.config import configs
from app.core.exceptions import TooManyRequestsError
from app.services.abuse_prevention_service import AbusePreventionService


class InMemoryRateLimitCounterBackend:
    def __init__(self):
        self._lock = threading.Lock()
        self.counters = {}
        self.ttl_seconds_seen = {}

    async def increment_and_get(
        self,
        scope_type: str,
        scope_value: str,
        window_name: str,
        window_start: datetime,
        ttl_seconds: int,
    ) -> int:
        with self._lock:
            key = (scope_type, scope_value, window_name, window_start)
            self.counters[key] = self.counters.get(key, 0) + 1
            self.ttl_seconds_seen[key] = ttl_seconds
            return self.counters[key]


def _set_default_limits(monkeypatch):
    monkeypatch.setattr(configs, "ABUSE_PREVENTION_ENABLED", True)
    monkeypatch.setattr(configs, "ABUSE_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(configs, "ABUSE_RATE_LIMIT_PER_API_KEY", 1000)
    monkeypatch.setattr(configs, "ABUSE_RATE_LIMIT_PER_IP", 1000)
    monkeypatch.setattr(configs, "ABUSE_RATE_LIMIT_PER_EXTERNAL_USER", 1000)
    monkeypatch.setattr(configs, "ABUSE_DAILY_QUOTA_PER_API_KEY", 1000)
    monkeypatch.setattr(configs, "RATE_LIMIT_TTL_BUFFER_SECONDS", 5)


def test_extract_client_ip_prefers_forwarded_header():
    backend = InMemoryRateLimitCounterBackend()
    service = AbusePreventionService(backend)
    request = SimpleNamespace(
        headers={"X-Forwarded-For": "198.51.100.20, 10.0.0.1"},
        client=SimpleNamespace(host="203.0.113.2"),
    )

    ip = service.extract_client_ip(request)

    assert ip == "198.51.100.20"


def test_window_bucket_start_is_deterministic():
    backend = InMemoryRateLimitCounterBackend()
    service = AbusePreventionService(backend)
    now = datetime(2026, 2, 10, 12, 0, 59, tzinfo=timezone.utc)

    bucket = service._get_window_bucket_start(now, 60)

    assert bucket == datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_enforce_limits_ignores_empty_scope_values(monkeypatch):
    _set_default_limits(monkeypatch)
    backend = InMemoryRateLimitCounterBackend()
    service = AbusePreventionService(backend)

    await service.enforce_task_mutation_limits(
        api_key=None,
        client_ip="  ",
        external_user_id="",
        now=datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert backend.counters == {}


@pytest.mark.asyncio
async def test_enforce_limits_raises_when_api_key_rate_limit_is_exceeded(monkeypatch):
    _set_default_limits(monkeypatch)
    monkeypatch.setattr(configs, "ABUSE_RATE_LIMIT_PER_API_KEY", 1)
    backend = InMemoryRateLimitCounterBackend()
    service = AbusePreventionService(backend)
    now = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)

    await service.enforce_task_mutation_limits(
        api_key="k-1", client_ip=None, external_user_id=None, now=now
    )

    with pytest.raises(TooManyRequestsError):
        await service.enforce_task_mutation_limits(
            api_key="k-1", client_ip=None, external_user_id=None, now=now
        )


@pytest.mark.asyncio
async def test_enforce_limits_raises_when_daily_quota_is_exceeded(monkeypatch):
    _set_default_limits(monkeypatch)
    monkeypatch.setattr(configs, "ABUSE_DAILY_QUOTA_PER_API_KEY", 1)
    backend = InMemoryRateLimitCounterBackend()
    service = AbusePreventionService(backend)
    now = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)

    await service.enforce_task_mutation_limits(
        api_key="k-1",
        client_ip="203.0.113.4",
        external_user_id="user_1",
        now=now,
    )

    with pytest.raises(TooManyRequestsError):
        await service.enforce_task_mutation_limits(
            api_key="k-1",
            client_ip="203.0.113.4",
            external_user_id="user_1",
            now=now,
        )


@pytest.mark.asyncio
async def test_enforce_limits_is_stable_under_concurrency(monkeypatch):
    _set_default_limits(monkeypatch)
    backend = InMemoryRateLimitCounterBackend()
    service = AbusePreventionService(backend)
    now = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)

    async def _run_once():
        await service.enforce_task_mutation_limits(
            api_key="k-1",
            client_ip="203.0.113.5",
            external_user_id="user_2",
            now=now,
        )

    await asyncio.gather(*[_run_once() for _ in range(20)])

    short_window_name = "task_mutation_short_60s"
    daily_window_name = "task_mutation_daily"
    short_bucket = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)
    daily_bucket = datetime(2026, 2, 10, 0, 0, 0, tzinfo=timezone.utc)

    api_key_short = ("api_key", "k-1", short_window_name, short_bucket)
    ip_short = ("ip", "203.0.113.5", short_window_name, short_bucket)
    user_short = ("external_user", "user_2", short_window_name, short_bucket)
    api_key_daily = ("api_key", "k-1", daily_window_name, daily_bucket)

    assert backend.counters[api_key_short] == 20
    assert backend.counters[ip_short] == 20
    assert backend.counters[user_short] == 20
    assert backend.counters[api_key_daily] == 20


@pytest.mark.asyncio
async def test_enforce_limits_passes_window_aware_ttl_to_backend(monkeypatch):
    _set_default_limits(monkeypatch)
    monkeypatch.setattr(configs, "RATE_LIMIT_TTL_BUFFER_SECONDS", 5)
    backend = InMemoryRateLimitCounterBackend()
    service = AbusePreventionService(backend)
    now = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)

    await service.enforce_task_mutation_limits(
        api_key="k-1",
        client_ip="203.0.113.6",
        external_user_id="user_3",
        now=now,
    )

    short_window_name = "task_mutation_short_60s"
    daily_window_name = "task_mutation_daily"
    short_bucket = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)
    daily_bucket = datetime(2026, 2, 10, 0, 0, 0, tzinfo=timezone.utc)

    # short window TTL = window_seconds (60) + buffer (5)
    assert backend.ttl_seconds_seen[
        ("api_key", "k-1", short_window_name, short_bucket)
    ] == 65
    # daily TTL = 86400 + buffer (5)
    assert backend.ttl_seconds_seen[
        ("api_key", "k-1", daily_window_name, daily_bucket)
    ] == 86405
