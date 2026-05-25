from threading import Lock
from time import monotonic
from types import SimpleNamespace
from typing import Optional

from fastapi import Security
from fastapi.security.api_key import APIKeyHeader

from app.core.config import configs
from app.core.exceptions import ForbiddenError, NotFoundError
from app.repository.apikey_repository import ApiKeyRepository
from app.services.base_service import BaseService
from app.util.generate_api_key import (GeneratedApiKey, generate_api_key,
                                       hash_api_key)
from app.util.response import Response

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


class ApiKeyService(BaseService):
    """
    Service class for API keys.

    Plaintext keys are surfaced to the caller exactly once at creation and
    never persisted. Authentication compares the sha256 hash of the value
    presented in the ``X-API-Key`` header against the canonical
    ``apiKeyHash`` column.

    Attributes:
        apikey_repository (ApiKeyRepository): Repository instance for API
          keys.
    """

    _header_cache = {}
    _cache_lock = Lock()

    def __init__(self, apikey_repository: ApiKeyRepository):
        """
        Initializes the ApiKeyService with the provided repository.

        Args:
            apikey_repository (ApiKeyRepository): The repository instance.
        """
        self.apikey_repository = apikey_repository
        super().__init__(apikey_repository)

    async def generate_api_key_service(self) -> GeneratedApiKey:
        """
        Generate a cryptographically-secure API key whose prefix and hash do
        not collide with any existing record.

        Returns:
            GeneratedApiKey: plaintext (shown once), public prefix, and
            sha256 hash.
        """
        while True:
            generated = generate_api_key()
            hash_collision = self.apikey_repository.read_by_column(
                "apiKeyHash",
                generated.key_hash,
                not_found_raise_exception=False,
            )
            if hash_collision is not None:
                continue
            prefix_collision = self.apikey_repository.read_by_column(
                "apiKey",
                generated.prefix,
                not_found_raise_exception=False,
            )
            if prefix_collision is None:
                return generated

    async def create_api_key(self, apikeyPostBody):
        """
        Persist a new API key record.

        Args:
            apikeyPostBody: The schema with prefix + hash + metadata.

        Returns:
            The created API key row.
        """
        return await self.apikey_repository.create(apikeyPostBody)

    def get_all_api_keys(self):
        """
        Get all API keys.

        Returns:
            List[ApiKey]: All API keys.
        """
        return self.apikey_repository.read_all()

    def revoke_api_key_by_prefix(self, prefix: str):
        """
        Revoke an API key identified by its public prefix.

        Args:
            prefix (str): The public prefix (e.g. ``gme_live_abc12345``).

        Returns:
            The updated row.

        Raises:
            NotFoundError: when the prefix does not match any record.
        """
        row = self.apikey_repository.read_by_column(
            "apiKey", prefix, not_found_raise_exception=False
        )
        if row is None:
            raise NotFoundError(detail=f"API key not found: {prefix}")
        updated = self.apikey_repository.update_attr(row.id, "active", False)
        ApiKeyService.clear_header_cache()
        return updated

    @staticmethod
    def get_api_key_header(
        api_key: str = Security(api_key_header),
    ):
        from app.core.container import Container

        """
        Authenticate a request based on the value of the ``X-API-Key``
        header. The value is hashed and compared against the canonical
        ``apiKeyHash`` column; the plaintext is never stored or returned.
        """
        if api_key is None:
            return Response.fail(error=ForbiddenError("API key not provided."))
        key_hash = hash_api_key(api_key)
        cached_api_key = ApiKeyService._get_cached_api_key(key_hash)
        if cached_api_key is not None:
            return Response.ok(data=cached_api_key)
        api_key_Repository = Container.apikey_repository()
        api_key_in_db = api_key_Repository.read_by_column(
            "apiKeyHash", key_hash, not_found_raise_exception=False
        )
        if api_key_in_db is None:
            raise ForbiddenError("API key is invalid or does not exist.")
        if not api_key_in_db.active:
            raise ForbiddenError(
                "API key is inactive. Please contact an admin."
            )
        normalized = SimpleNamespace(
            apiKey=api_key_in_db.apiKey, active=api_key_in_db.active
        )
        ApiKeyService._set_cached_api_key(key_hash, normalized)
        return Response.ok(data=normalized)

    @classmethod
    def _get_cache_ttl_seconds(cls) -> int:
        ttl = int(getattr(configs, "API_KEY_HEADER_CACHE_TTL_SECONDS", 0))
        return ttl if ttl > 0 else 0

    @classmethod
    def _get_cached_api_key(cls, cache_key: str) -> Optional[SimpleNamespace]:
        ttl_seconds = cls._get_cache_ttl_seconds()
        if ttl_seconds <= 0:
            return None
        now = monotonic()
        with cls._cache_lock:
            cache_entry = cls._header_cache.get(cache_key)
            if cache_entry is None:
                return None
            expires_at, cached_value = cache_entry
            if expires_at <= now:
                cls._header_cache.pop(cache_key, None)
                return None
            return cached_value

    @classmethod
    def _set_cached_api_key(cls, cache_key: str, api_key_data) -> None:
        ttl_seconds = cls._get_cache_ttl_seconds()
        if ttl_seconds <= 0:
            return
        expires_at = monotonic() + ttl_seconds
        with cls._cache_lock:
            cls._header_cache[cache_key] = (expires_at, api_key_data)

    @classmethod
    def clear_header_cache(cls) -> None:
        with cls._cache_lock:
            cls._header_cache.clear()
