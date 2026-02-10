from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import threading
from types import SimpleNamespace

import pytest

from app.core.config import configs
from app.core.exceptions import TooManyRequestsError
from app.services.abuse_prevention_service import AbusePreventionService


class InMemoryAbuseLimitCounterRepository:
    def __init__(self):
        self._lock = threading.Lock()
        self.counters = {}

    def increment_and_get(
        self,
        scope_type: str,
        scope_value: str,
        window_name: str,
        window_start: datetime,
    ) -> int:
        with self._lock:
            key = (scope_type, scope_value, window_name, window_start)
            self.counters[key] = self.counters.get(key, 0) + 1
            return self.counters[key]


def _set_default_limits(monkeypatch):
    monkeypatch.setattr(configs, "ABUSE_PREVENTION_ENABLED", True)
    monkeypatch.setattr(configs, "ABUSE_RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr(configs, "ABUSE_RATE_LIMIT_PER_API_KEY", 1000)
    monkeypatch.setattr(configs, "ABUSE_RATE_LIMIT_PER_IP", 1000)
    monkeypatch.setattr(configs, "ABUSE_RATE_LIMIT_PER_EXTERNAL_USER", 1000)
    monkeypatch.setattr(configs, "ABUSE_DAILY_QUOTA_PER_API_KEY", 1000)


def test_extract_client_ip_prefers_forwarded_header():
    repository = InMemoryAbuseLimitCounterRepository()
    service = AbusePreventionService(repository)
    request = SimpleNamespace(
        headers={"X-Forwarded-For": "198.51.100.20, 10.0.0.1"},
        client=SimpleNamespace(host="203.0.113.2"),
    )

    ip = service.extract_client_ip(request)

    assert ip == "198.51.100.20"


def test_window_bucket_start_is_deterministic():
    repository = InMemoryAbuseLimitCounterRepository()
    service = AbusePreventionService(repository)
    now = datetime(2026, 2, 10, 12, 0, 59, tzinfo=timezone.utc)

    bucket = service._get_window_bucket_start(now, 60)

    assert bucket == datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)


def test_enforce_limits_ignores_empty_scope_values(monkeypatch):
    _set_default_limits(monkeypatch)
    repository = InMemoryAbuseLimitCounterRepository()
    service = AbusePreventionService(repository)

    service.enforce_task_mutation_limits(
        api_key=None,
        client_ip="  ",
        external_user_id="",
        now=datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert repository.counters == {}


def test_enforce_limits_raises_when_api_key_rate_limit_is_exceeded(monkeypatch):
    _set_default_limits(monkeypatch)
    monkeypatch.setattr(configs, "ABUSE_RATE_LIMIT_PER_API_KEY", 1)
    repository = InMemoryAbuseLimitCounterRepository()
    service = AbusePreventionService(repository)
    now = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)

    service.enforce_task_mutation_limits(
        api_key="k-1", client_ip=None, external_user_id=None, now=now
    )

    with pytest.raises(TooManyRequestsError):
        service.enforce_task_mutation_limits(
            api_key="k-1", client_ip=None, external_user_id=None, now=now
        )


def test_enforce_limits_raises_when_daily_quota_is_exceeded(monkeypatch):
    _set_default_limits(monkeypatch)
    monkeypatch.setattr(configs, "ABUSE_DAILY_QUOTA_PER_API_KEY", 1)
    repository = InMemoryAbuseLimitCounterRepository()
    service = AbusePreventionService(repository)
    now = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)

    service.enforce_task_mutation_limits(
        api_key="k-1",
        client_ip="203.0.113.4",
        external_user_id="user_1",
        now=now,
    )

    with pytest.raises(TooManyRequestsError):
        service.enforce_task_mutation_limits(
            api_key="k-1",
            client_ip="203.0.113.4",
            external_user_id="user_1",
            now=now,
        )


def test_enforce_limits_is_stable_under_concurrency(monkeypatch):
    _set_default_limits(monkeypatch)
    repository = InMemoryAbuseLimitCounterRepository()
    service = AbusePreventionService(repository)
    now = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)

    def _run_once():
        service.enforce_task_mutation_limits(
            api_key="k-1",
            client_ip="203.0.113.5",
            external_user_id="user_2",
            now=now,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda _: _run_once(), range(20)))

    short_window_name = "task_mutation_short_60s"
    daily_window_name = "task_mutation_daily"
    short_bucket = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)
    daily_bucket = datetime(2026, 2, 10, 0, 0, 0, tzinfo=timezone.utc)

    assert repository.counters[("api_key", "k-1", short_window_name, short_bucket)] == 20
    assert repository.counters[("ip", "203.0.113.5", short_window_name, short_bucket)] == 20
    assert (
        repository.counters[
            ("external_user", "user_2", short_window_name, short_bucket)
        ]
        == 20
    )
    assert repository.counters[("api_key", "k-1", daily_window_name, daily_bucket)] == 20
