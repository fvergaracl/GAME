import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.container import Container
from app.core.exceptions import ForbiddenError, NotFoundError
from app.repository.apikey_repository import ApiKeyRepository
from app.services.apikey_cache_backend import InMemoryApiKeyCacheBackend
from app.services.apikey_service import ApiKeyService
from app.util.generate_api_key import GeneratedApiKey, hash_api_key


class TestApiKeyService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """
        Set up the test with a mock ApiKeyRepository instance.
        """
        ApiKeyService.clear_header_cache()
        self.apikey_repository = MagicMock(spec=ApiKeyRepository)
        self.cache_backend = InMemoryApiKeyCacheBackend()
        self.api_key_service = ApiKeyService(
            self.apikey_repository, cache_backend=self.cache_backend
        )

    @patch("app.services.apikey_service.generate_api_key")
    async def test_generate_api_key_returns_unique_triple(
        self, mock_generate_api_key
    ):
        """
        The service skips colliding hashes/prefixes and returns a
        plaintext/prefix/hash triple that does not exist in the DB.
        """
        first = GeneratedApiKey(
            plaintext="plain-1", prefix="prefix-1", key_hash="hash-1"
        )
        second = GeneratedApiKey(
            plaintext="plain-2", prefix="prefix-2", key_hash="hash-2"
        )
        mock_generate_api_key.side_effect = [first, second]
        # First lookup by hash returns a row (collision), second returns
        # None, then prefix lookup also returns None.
        self.apikey_repository.read_by_column.side_effect = [
            MagicMock(),  # hash collision on first
            None,         # hash miss on second
            None,         # prefix miss on second
        ]

        generated = await self.api_key_service.generate_api_key_service()

        self.assertEqual(generated, second)
        self.apikey_repository.read_by_column.assert_any_call(
            "apiKeyHash", "hash-1", not_found_raise_exception=False
        )
        self.apikey_repository.read_by_column.assert_any_call(
            "apiKeyHash", "hash-2", not_found_raise_exception=False
        )
        self.apikey_repository.read_by_column.assert_any_call(
            "apiKey", "prefix-2", not_found_raise_exception=False
        )

    async def test_create_api_key_successfully(self):
        """
        Test that the create_api_key method delegates to the repository.
        """
        api_key_data = {
            "apiKey": "gme_live_abcdefgh",
            "apiKeyHash": "abc",
            "description": "Test API key",
        }

        self.apikey_repository.create.return_value = api_key_data

        created_api_key = await self.api_key_service.create_api_key(
            api_key_data
        )

        self.apikey_repository.create.assert_called_once_with(api_key_data)
        self.assertEqual(created_api_key, api_key_data)

    async def test_get_all_api_keys_successfully(self):
        api_keys = [
            {"apiKey": "gme_live_aaaaaaaa", "description": "Test API key 1"},
            {"apiKey": "gme_live_bbbbbbbb", "description": "Test API key 2"},
        ]
        self.apikey_repository.read_all.return_value = api_keys

        retrieved_api_keys = await self.api_key_service.get_all_api_keys()

        self.apikey_repository.read_all.assert_called_once()
        self.assertEqual(retrieved_api_keys, api_keys)

    async def test_revoke_api_key_by_prefix_deactivates_row(self):
        row = MagicMock(id="row-1", active=True, apiKeyHash="hash-1")
        self.apikey_repository.read_by_column.return_value = row
        self.apikey_repository.update_attr.return_value = MagicMock(
            id="row-1", active=False, apiKey="gme_live_abcdefgh"
        )

        result = await self.api_key_service.revoke_api_key_by_prefix(
            "gme_live_abcdefgh"
        )

        self.apikey_repository.read_by_column.assert_called_once_with(
            "apiKey",
            "gme_live_abcdefgh",
            not_found_raise_exception=False,
        )
        self.apikey_repository.update_attr.assert_called_once_with(
            "row-1", "active", False
        )
        self.assertFalse(result.active)

    async def test_revoke_api_key_by_prefix_deletes_only_targeted_cache_entry(
        self,
    ):
        # Two cached entries; revoking one must leave the other intact.
        await self.cache_backend.set(
            "hash-1",
            SimpleNamespace(apiKey="gme_live_aaaaaaaa", active=True),
            ttl_seconds=60,
        )
        await self.cache_backend.set(
            "hash-2",
            SimpleNamespace(apiKey="gme_live_bbbbbbbb", active=True),
            ttl_seconds=60,
        )

        row = MagicMock(id="row-1", active=True, apiKeyHash="hash-1")
        self.apikey_repository.read_by_column.return_value = row
        self.apikey_repository.update_attr.return_value = MagicMock(
            id="row-1", active=False, apiKey="gme_live_aaaaaaaa"
        )

        await self.api_key_service.revoke_api_key_by_prefix(
            "gme_live_aaaaaaaa"
        )

        self.assertIsNone(await self.cache_backend.get("hash-1"))
        survivor = await self.cache_backend.get("hash-2")
        self.assertIsNotNone(survivor)
        self.assertEqual(survivor.apiKey, "gme_live_bbbbbbbb")

    async def test_revoke_api_key_by_prefix_raises_when_missing(self):
        self.apikey_repository.read_by_column.return_value = None

        with self.assertRaises(NotFoundError):
            await self.api_key_service.revoke_api_key_by_prefix(
                "gme_live_missing0"
            )

        self.apikey_repository.update_attr.assert_not_called()

    async def test_get_api_key_header_raises_when_api_key_does_not_exist(self):
        ApiKeyService.clear_header_cache()
        repository = AsyncMock()
        repository.read_by_column.return_value = None
        missing_plaintext = "missing-key"
        expected_hash = hash_api_key(missing_plaintext)

        with patch.object(
            Container,
            "apikey_repository",
            MagicMock(return_value=repository),
        ):
            with self.assertRaises(ForbiddenError) as exc_info:
                await ApiKeyService.get_api_key_header(missing_plaintext)

        repository.read_by_column.assert_called_once_with(
            "apiKeyHash", expected_hash, not_found_raise_exception=False
        )
        self.assertEqual(
            exc_info.exception.detail,
            "API key is invalid or does not exist.",
        )

    async def test_get_api_key_header_returns_fail_response_when_api_key_is_none(
        self,
    ):
        ApiKeyService.clear_header_cache()
        response = await ApiKeyService.get_api_key_header(None)

        self.assertFalse(response.sucess)
        self.assertIsInstance(response.error, ForbiddenError)
        self.assertEqual(response.error.detail, "API key not provided.")

    async def test_get_api_key_header_raises_when_api_key_is_inactive(self):
        ApiKeyService.clear_header_cache()
        repository = AsyncMock()
        repository.read_by_column.return_value = MagicMock(active=False)

        with patch.object(
            Container,
            "apikey_repository",
            MagicMock(return_value=repository),
        ):
            with self.assertRaises(ForbiddenError) as exc_info:
                await ApiKeyService.get_api_key_header("inactive-key")

        repository.read_by_column.assert_called_once_with(
            "apiKeyHash",
            hash_api_key("inactive-key"),
            not_found_raise_exception=False,
        )
        self.assertEqual(
            exc_info.exception.detail,
            "API key is inactive. Please contact an admin.",
        )

    async def test_get_api_key_header_returns_ok_with_prefix_only(self):
        ApiKeyService.clear_header_cache()
        api_key_in_db = MagicMock(active=True)
        api_key_in_db.apiKey = "gme_live_abcdefgh"
        repository = AsyncMock()
        repository.read_by_column.return_value = api_key_in_db

        with patch.object(
            Container,
            "apikey_repository",
            MagicMock(return_value=repository),
        ):
            response = await ApiKeyService.get_api_key_header(
                "gme_live_abcdefgh.SECRET-SECRET-SECRET-SECRET-SECRE"
            )

        repository.read_by_column.assert_called_once_with(
            "apiKeyHash",
            hash_api_key(
                "gme_live_abcdefgh.SECRET-SECRET-SECRET-SECRET-SECRE"
            ),
            not_found_raise_exception=False,
        )
        self.assertTrue(response.sucess)
        # Only the public prefix is propagated -- never the secret.
        self.assertEqual(response.data.apiKey, "gme_live_abcdefgh")
        self.assertTrue(response.data.active)

    async def test_get_api_key_header_uses_cache_for_repeated_requests(self):
        ApiKeyService.clear_header_cache()
        api_key_in_db = MagicMock(active=True)
        api_key_in_db.apiKey = "gme_live_cachedkk"
        repository = AsyncMock()
        repository.read_by_column.return_value = api_key_in_db

        with patch.object(
            Container,
            "apikey_repository",
            MagicMock(return_value=repository),
        ):
            first = await ApiKeyService.get_api_key_header(
                "gme_live_cachedkk.payload-payload-payload-payload-pa"
            )
            second = await ApiKeyService.get_api_key_header(
                "gme_live_cachedkk.payload-payload-payload-payload-pa"
            )

        self.assertTrue(first.sucess)
        self.assertTrue(second.sucess)
        repository.read_by_column.assert_called_once()


if __name__ == "__main__":
    unittest.main()
