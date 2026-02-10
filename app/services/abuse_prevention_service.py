from datetime import datetime, timezone
from typing import Optional

from fastapi import Request

from app.core.config import configs
from app.core.exceptions import TooManyRequestsError
from app.repository.abuse_limit_counter_repository import AbuseLimitCounterRepository


class AbusePreventionService:
    """
    Service responsible for abuse prevention checks on sensitive endpoints.
    """

    def __init__(self, abuse_limit_counter_repository: AbuseLimitCounterRepository):
        self.abuse_limit_counter_repository = abuse_limit_counter_repository

    @staticmethod
    def extract_client_ip(request: Optional[Request]) -> Optional[str]:
        """
        Extracts best-effort client IP from forwarding headers or socket info.
        """
        if request is None:
            return None

        forwarded_for = request.headers.get("X-Forwarded-For") or request.headers.get(
            "x-forwarded-for"
        )
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
            if client_ip:
                return client_ip

        real_ip = request.headers.get("X-Real-IP") or request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip() or None

        if request.client and request.client.host:
            return request.client.host
        return None

    def enforce_task_mutation_limits(
        self,
        api_key: Optional[str],
        client_ip: Optional[str],
        external_user_id: Optional[str],
        now: Optional[datetime] = None,
    ) -> None:
        """
        Enforces abuse controls for task mutation endpoints (`/points`, `/action`).
        """
        if not configs.ABUSE_PREVENTION_ENABLED:
            return

        now = self._normalize_now(now)
        window_seconds = max(1, int(configs.ABUSE_RATE_LIMIT_WINDOW_SECONDS))
        short_window_name = f"task_mutation_short_{window_seconds}s"
        short_window_start = self._get_window_bucket_start(now, window_seconds)

        normalized_api_key = self._normalize_scope_value(api_key)
        normalized_ip = self._normalize_scope_value(client_ip)
        normalized_external_user = self._normalize_scope_value(external_user_id)

        self._enforce_limit(
            scope_type="api_key",
            scope_value=normalized_api_key,
            window_name=short_window_name,
            window_start=short_window_start,
            max_allowed=int(configs.ABUSE_RATE_LIMIT_PER_API_KEY),
            error_detail="API key rate limit exceeded for sensitive task operations.",
        )
        self._enforce_limit(
            scope_type="ip",
            scope_value=normalized_ip,
            window_name=short_window_name,
            window_start=short_window_start,
            max_allowed=int(configs.ABUSE_RATE_LIMIT_PER_IP),
            error_detail="IP rate limit exceeded for sensitive task operations.",
        )
        self._enforce_limit(
            scope_type="external_user",
            scope_value=normalized_external_user,
            window_name=short_window_name,
            window_start=short_window_start,
            max_allowed=int(configs.ABUSE_RATE_LIMIT_PER_EXTERNAL_USER),
            error_detail="externalUserId rate limit exceeded for sensitive task operations.",
        )

        daily_window_name = "task_mutation_daily"
        daily_window_start = self._get_daily_bucket_start(now)
        self._enforce_limit(
            scope_type="api_key",
            scope_value=normalized_api_key,
            window_name=daily_window_name,
            window_start=daily_window_start,
            max_allowed=int(configs.ABUSE_DAILY_QUOTA_PER_API_KEY),
            error_detail="Daily API key quota exceeded for sensitive task operations.",
        )

    def _enforce_limit(
        self,
        scope_type: str,
        scope_value: Optional[str],
        window_name: str,
        window_start: datetime,
        max_allowed: int,
        error_detail: str,
    ) -> None:
        if not scope_value:
            return
        if max_allowed <= 0:
            return

        counter = self.abuse_limit_counter_repository.increment_and_get(
            scope_type=scope_type,
            scope_value=scope_value,
            window_name=window_name,
            window_start=window_start,
        )
        if counter > max_allowed:
            raise TooManyRequestsError(detail=error_detail)

    @staticmethod
    def _normalize_scope_value(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        return normalized

    @staticmethod
    def _normalize_now(now: Optional[datetime]) -> datetime:
        if now is None:
            return datetime.now(timezone.utc)
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone.utc)
        return now.astimezone(timezone.utc)

    @staticmethod
    def _get_window_bucket_start(now: datetime, window_seconds: int) -> datetime:
        now = now.astimezone(timezone.utc)
        unix_now = int(now.timestamp())
        bucket_start = unix_now - (unix_now % window_seconds)
        return datetime.fromtimestamp(bucket_start, tz=timezone.utc)

    @staticmethod
    def _get_daily_bucket_start(now: datetime) -> datetime:
        now = now.astimezone(timezone.utc)
        return datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            tzinfo=timezone.utc,
        )
