from types import SimpleNamespace
from typing import Any, Optional

from fastapi import Security
from fastapi.security.api_key import APIKeyHeader

from app.core.config import configs
from app.core.exceptions import ForbiddenError, NotFoundError
from app.repository.apikey_repository import ApiKeyRepository
from app.services.apikey_cache_backend import (
    ApiKeyCacheBackend,
    InMemoryApiKeyCacheBackend,
)
from app.services.base_service import BaseService
from app.util.generate_api_key import GeneratedApiKey, generate_api_key, hash_api_key
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

    Revocation consistency depends on ``configs.APIKEY_CACHE_BACKEND``:

    - ``redis`` (recommended for multi-worker deployments): cache entries
      live in a shared Redis keyspace, so a revoke on any worker is
      observed by every other worker on its next request.
    - ``memory`` (default, single process): each gunicorn worker keeps its
      own dict; revocations only invalidate the local worker's entry and
      remote workers continue serving the cached value until the TTL
      (``API_KEY_HEADER_CACHE_TTL_SECONDS``, default 5s) expires.

    Attributes:
        apikey_repository (ApiKeyRepository): Repository instance for API
          keys.
        cache_backend (ApiKeyCacheBackend): Backing store for the resolved
          ``(apiKey, active)`` tuple keyed by sha256 hash.
    """

    def __init__(
        self,
        apikey_repository: ApiKeyRepository,
        cache_backend: Optional[ApiKeyCacheBackend] = None,
    ) -> None:
        """
        Initializes the ApiKeyService with the provided repository and cache.

        Args:
            apikey_repository: The repository instance.
            cache_backend: The cache backend. Defaults to a fresh in-process
              instance so direct instantiation (mostly tests) keeps working
              without wiring through the DI container.
        """
        self.apikey_repository = apikey_repository
        self.cache_backend = cache_backend or InMemoryApiKeyCacheBackend()
        super().__init__(apikey_repository)

    async def generate_api_key_service(self) -> GeneratedApiKey:
        """
        Generate a cryptographically-secure API key whose prefix and hash do
        not collide with any existing record.
        """
        while True:
            generated = generate_api_key()
            hash_collision = await self.apikey_repository.read_by_column(
                "apiKeyHash",
                generated.key_hash,
                not_found_raise_exception=False,
            )
            if hash_collision is not None:
                continue
            prefix_collision = await self.apikey_repository.read_by_column(
                "apiKey",
                generated.prefix,
                not_found_raise_exception=False,
            )
            if prefix_collision is None:
                return generated

    async def create_api_key(self, apikeyPostBody) -> Any:
        """
        Persist a new API-key record.

        Args:
            apikeyPostBody: Schema describing the API key to store (including
                its prefix and hash).

        Returns:
            Any: The created API-key entity.
        """
        return await self.apikey_repository.create(apikeyPostBody)

    async def get_all_api_keys(self) -> Any:
        """
        Return every API-key record.

        Returns:
            Any: All stored API-key entities.
        """
        return await self.apikey_repository.read_all()

    async def revoke_api_key_by_prefix(self, prefix: str) -> Any:
        """
        Revoke an API key identified by its public prefix and drop the
        matching cache entry. The deactivated row's ``apiKeyHash`` is the
        exact cache key used by ``get_api_key_header`` (both are
        ``hash_api_key(plaintext)``), so a precise ``delete`` is enough --
        no need to nuke unrelated entries.
        """
        row = await self.apikey_repository.read_by_column(
            "apiKey", prefix, not_found_raise_exception=False
        )
        if row is None:
            raise NotFoundError(detail=f"API key not found: {prefix}")
        updated = await self.apikey_repository.update_attr(row.id, "active", False)
        cache_key = getattr(row, "apiKeyHash", None)
        if cache_key:
            await self.cache_backend.delete(cache_key)
        return updated

    @staticmethod
    async def get_api_key_header(
        api_key: str = Security(api_key_header),
    ) -> Response:
        """
        Authenticate a request based on the value of the ``X-API-Key``
        header. The value is hashed and compared against the canonical
        ``apiKeyHash`` column; the plaintext is never stored or returned.

        A short-lived cache (when ``API_KEY_HEADER_CACHE_TTL_SECONDS`` > 0)
        avoids a DB lookup on every request.

        Args:
            api_key (str): The raw ``X-API-Key`` header value.

        Returns:
            Response: ``Response.ok`` with the normalized key info on success,
            or ``Response.fail`` when the header is absent.

        Raises:
            ForbiddenError: If the key is missing, unknown or inactive.
        """
        from app.core.container import Container

        if api_key is None:
            return Response.fail(error=ForbiddenError("API key not provided."))
        key_hash = hash_api_key(api_key)
        cache_backend = Container.apikey_cache_backend()
        ttl_seconds = int(getattr(configs, "API_KEY_HEADER_CACHE_TTL_SECONDS", 0) or 0)
        if ttl_seconds > 0:
            cached = await cache_backend.get(key_hash)
            if cached is not None:
                return Response.ok(data=cached)
        api_key_Repository = Container.apikey_repository()
        api_key_in_db = await api_key_Repository.read_by_column(
            "apiKeyHash", key_hash, not_found_raise_exception=False
        )
        if api_key_in_db is None:
            raise ForbiddenError("API key is invalid or does not exist.")
        if not api_key_in_db.active:
            raise ForbiddenError("API key is inactive. Please contact an admin.")
        normalized = SimpleNamespace(
            apiKey=api_key_in_db.apiKey, active=api_key_in_db.active
        )
        if ttl_seconds > 0:
            await cache_backend.set(key_hash, normalized, ttl_seconds)
        return Response.ok(data=normalized)

    @classmethod
    def clear_header_cache(cls) -> None:
        """
        Reset the cache synchronously. Only the in-memory backend can be
        cleared without an event loop; for the Redis backend, prefer the
        async ``await backend.clear()`` (or rely on per-entry deletion via
        ``revoke_api_key_by_prefix``). Kept as a classmethod so existing
        tests can call it from ``setUp`` for isolation.
        """
        from app.core.container import Container

        try:
            backend = Container.apikey_cache_backend()
        except Exception:
            return
        if isinstance(backend, InMemoryApiKeyCacheBackend):
            backend.sync_clear()
