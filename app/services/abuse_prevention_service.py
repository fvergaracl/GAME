import ipaddress
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request

from app.core.config import configs
from app.core.exceptions import TooManyRequestsError
from app.services.rate_limit_counter_backend import RateLimitCounterBackend


class AbusePreventionService:
    """
    Service responsible for abuse prevention checks on sensitive endpoints.
    """

    def __init__(self, counter_backend: RateLimitCounterBackend) -> None:
        self.counter_backend = counter_backend

    @staticmethod
    def extract_client_ip(request: Optional[Request]) -> Optional[str]:
        """
        Extracts the best-effort client IP.

        X-Forwarded-For and X-Real-IP are honored only when the direct
        socket peer is in ``configs.TRUSTED_PROXY_IPS``. Without that
        gate any client can forge these headers and bypass per-IP rate
        limiting (see security finding H10). When the peer is trusted,
        X-Forwarded-For is walked right-to-left, skipping further
        trusted hops, to find the leftmost untrusted address.
        """
        if request is None:
            return None

        direct_peer = (
            request.client.host if request.client and request.client.host else None
        )

        if not AbusePreventionService._peer_is_trusted_proxy(direct_peer):
            return direct_peer

        forwarded_for = request.headers.get("X-Forwarded-For") or request.headers.get(
            "x-forwarded-for"
        )
        if forwarded_for:
            for raw in reversed(forwarded_for.split(",")):
                candidate = raw.strip()
                if not candidate:
                    continue
                try:
                    ipaddress.ip_address(candidate)
                except ValueError:
                    continue
                if not AbusePreventionService._peer_is_trusted_proxy(candidate):
                    return candidate

        real_ip = request.headers.get("X-Real-IP") or request.headers.get("x-real-ip")
        if real_ip:
            candidate = real_ip.strip()
            if candidate:
                try:
                    ipaddress.ip_address(candidate)
                    return candidate
                except ValueError:
                    pass

        return direct_peer

    @staticmethod
    def _peer_is_trusted_proxy(ip: Optional[str]) -> bool:
        """
        Return whether ``ip`` falls within a configured trusted-proxy network.

        Used to decide if ``X-Forwarded-For`` can be trusted to derive the real
        client IP.

        Args:
            ip (Optional[str]): The direct peer IP to test.

        Returns:
            bool: ``True`` if ``ip`` is valid and within ``TRUSTED_PROXY_IPS``.
        """
        if not ip:
            return False
        trusted = configs.TRUSTED_PROXY_IPS
        if not trusted:
            return False
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return False
        return any(addr in network for network in trusted)

    async def enforce_task_mutation_limits(
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
        short_ttl = self._ttl_for_seconds(window_seconds)

        normalized_api_key = self._normalize_scope_value(api_key)
        normalized_ip = self._normalize_scope_value(client_ip)
        normalized_external_user = self._normalize_scope_value(external_user_id)

        await self._enforce_limit(
            scope_type="api_key",
            scope_value=normalized_api_key,
            window_name=short_window_name,
            window_start=short_window_start,
            ttl_seconds=short_ttl,
            max_allowed=int(configs.ABUSE_RATE_LIMIT_PER_API_KEY),
            error_detail="API key rate limit exceeded for sensitive task operations.",
        )
        await self._enforce_limit(
            scope_type="ip",
            scope_value=normalized_ip,
            window_name=short_window_name,
            window_start=short_window_start,
            ttl_seconds=short_ttl,
            max_allowed=int(configs.ABUSE_RATE_LIMIT_PER_IP),
            error_detail="IP rate limit exceeded for sensitive task operations.",
        )
        await self._enforce_limit(
            scope_type="external_user",
            scope_value=normalized_external_user,
            window_name=short_window_name,
            window_start=short_window_start,
            ttl_seconds=short_ttl,
            max_allowed=int(configs.ABUSE_RATE_LIMIT_PER_EXTERNAL_USER),
            error_detail="externalUserId rate limit exceeded for sensitive task operations.",
        )

        daily_window_name = "task_mutation_daily"
        daily_window_start = self._get_daily_bucket_start(now)
        daily_ttl = self._ttl_for_seconds(86400)
        await self._enforce_limit(
            scope_type="api_key",
            scope_value=normalized_api_key,
            window_name=daily_window_name,
            window_start=daily_window_start,
            ttl_seconds=daily_ttl,
            max_allowed=int(configs.ABUSE_DAILY_QUOTA_PER_API_KEY),
            error_detail="Daily API key quota exceeded for sensitive task operations.",
        )

    async def _enforce_limit(
        self,
        scope_type: str,
        scope_value: Optional[str],
        window_name: str,
        window_start: datetime,
        ttl_seconds: int,
        max_allowed: int,
        error_detail: str,
    ) -> None:
        """
        Increment one rate-limit bucket and raise if it exceeds the cap.

        No-ops when the scope value is empty or the cap is non-positive.

        Args:
            scope_type (str): Dimension being limited (``api_key``/``ip``/...).
            scope_value (Optional[str]): Concrete value within ``scope_type``.
            window_name (str): Name of the time window/bucket.
            window_start (datetime): Start of the bucket window.
            ttl_seconds (int): TTL applied to the bucket.
            max_allowed (int): Maximum requests allowed in the window.
            error_detail (str): Message used when the limit is exceeded.

        Raises:
            TooManyRequestsError: If the counter exceeds ``max_allowed``.
        """
        if not scope_value:
            return
        if max_allowed <= 0:
            return

        counter = await self.counter_backend.increment_and_get(
            scope_type=scope_type,
            scope_value=scope_value,
            window_name=window_name,
            window_start=window_start,
            ttl_seconds=ttl_seconds,
        )
        if counter > max_allowed:
            raise TooManyRequestsError(detail=error_detail)

    @staticmethod
    def _normalize_scope_value(value: Optional[str]) -> Optional[str]:
        """
        Trim a scope value, collapsing blanks to ``None``.

        Args:
            value (Optional[str]): Raw scope value.

        Returns:
            Optional[str]: The stripped value, or ``None`` if empty/blank.
        """
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        return normalized

    @staticmethod
    def _normalize_now(now: Optional[datetime]) -> datetime:
        """
        Return ``now`` as a UTC-aware datetime, defaulting to the current time.

        Args:
            now (Optional[datetime]): Caller-supplied time, naive or aware.

        Returns:
            datetime: A timezone-aware UTC datetime.
        """
        if now is None:
            return datetime.now(timezone.utc)
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone.utc)
        return now.astimezone(timezone.utc)

    @staticmethod
    def _get_window_bucket_start(now: datetime, window_seconds: int) -> datetime:
        """
        Align ``now`` down to the start of its fixed-size time bucket.

        Args:
            now (datetime): The reference time.
            window_seconds (int): Bucket width in seconds.

        Returns:
            datetime: UTC start of the bucket containing ``now``.
        """
        now = now.astimezone(timezone.utc)
        unix_now = int(now.timestamp())
        bucket_start = unix_now - (unix_now % window_seconds)
        return datetime.fromtimestamp(bucket_start, tz=timezone.utc)

    @staticmethod
    def _get_daily_bucket_start(now: datetime) -> datetime:
        """
        Return midnight UTC of ``now``'s day (the daily-quota bucket start).

        Args:
            now (datetime): The reference time.

        Returns:
            datetime: UTC start of the current day.
        """
        now = now.astimezone(timezone.utc)
        return datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            tzinfo=timezone.utc,
        )

    @staticmethod
    def _ttl_for_seconds(window_seconds: int) -> int:
        """
        Compute a bucket TTL from a window length plus a skew buffer.

        Args:
            window_seconds (int): The window length in seconds.

        Returns:
            int: TTL in seconds (window plus ``RATE_LIMIT_TTL_BUFFER_SECONDS``)
            so buckets survive clock skew between instances and Redis.
        """
        # Extra buffer absorbs clock skew between API instances and Redis so
        # a bucket cannot die just before the next request promotes it.
        buffer = max(1, int(configs.RATE_LIMIT_TTL_BUFFER_SECONDS))
        return max(1, int(window_seconds)) + buffer
