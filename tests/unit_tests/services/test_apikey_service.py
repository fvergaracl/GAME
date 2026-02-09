import unittest
from unittest.mock import MagicMock, patch

from app.core.container import Container
from app.core.exceptions import ForbiddenError
from app.repository.apikey_repository import ApiKeyRepository
from app.services.apikey_service import ApiKeyService


class TestApiKeyService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """
        Set up the test with a mock ApiKeyRepository instance.
        """
        self.apikey_repository = MagicMock(spec=ApiKeyRepository)
        self.api_key_service = ApiKeyService(self.apikey_repository)

    @patch("app.services.apikey_service.generate_api_key")
    async def test_generate_api_key_creates_unique_key(self, mock_generate_api_key):
        """
        Test that the generate_api_key_service method generates a unique API
          key.
        """
        mock_generate_api_key.side_effect = ["key_1", "key_2"]
        self.apikey_repository.read_by_column.side_effect = [True, None]

        generated_api_key = await self.api_key_service.generate_api_key_service()

        self.assertEqual(mock_generate_api_key.call_count, 2)
        self.assertEqual(generated_api_key, "key_2")

        self.apikey_repository.read_by_column.assert_any_call(
            "apiKey", "key_1", not_found_raise_exception=False
        )
        self.apikey_repository.read_by_column.assert_any_call(
            "apiKey", "key_2", not_found_raise_exception=False
        )

    async def test_create_api_key_successfully(self):
        """
        Test that the create_api_key method successfully creates a new API key.
        """
        api_key_data = {"apiKey": "new_api_key", "description": "Test API key"}

        self.apikey_repository.create.return_value = api_key_data

        created_api_key = await self.api_key_service.create_api_key(api_key_data)

        self.apikey_repository.create.assert_called_once_with(api_key_data)

        self.assertEqual(created_api_key, api_key_data)

    def test_get_all_api_keys_successfully(self):
        """
        Test that the get_all_api_keys method retrieves all API keys correctly.
        """
        api_keys = [
            {"apiKey": "api_key_1", "description": "Test API key 1"},
            {"apiKey": "api_key_2", "description": "Test API key 2"},
        ]

        self.apikey_repository.read_all.return_value = api_keys

        retrieved_api_keys = self.api_key_service.get_all_api_keys()

        self.apikey_repository.read_all.assert_called_once()

        self.assertEqual(retrieved_api_keys, api_keys)

    def test_get_api_key_header_raises_when_api_key_does_not_exist(self):
        repository = MagicMock()
        repository.read_by_column.return_value = None

        with patch.object(
            Container, "apikey_repository", MagicMock(return_value=repository)
        ):
            with self.assertRaises(ForbiddenError) as exc_info:
                ApiKeyService.get_api_key_header("missing-key")

        repository.read_by_column.assert_called_once_with(
            "apiKey", "missing-key", not_found_raise_exception=False
        )
        self.assertEqual(
            exc_info.exception.detail,
            "API key is invalid or does not exist.",
        )

    def test_get_api_key_header_returns_fail_response_when_api_key_is_none(self):
        response = ApiKeyService.get_api_key_header(None)

        self.assertFalse(response.sucess)
        self.assertIsInstance(response.error, ForbiddenError)
        self.assertEqual(response.error.detail, "API key not provided.")

    def test_get_api_key_header_raises_when_api_key_is_inactive(self):
        repository = MagicMock()
        repository.read_by_column.return_value = MagicMock(active=False)

        with patch.object(
            Container, "apikey_repository", MagicMock(return_value=repository)
        ):
            with self.assertRaises(ForbiddenError) as exc_info:
                ApiKeyService.get_api_key_header("inactive-key")

        repository.read_by_column.assert_called_once_with(
            "apiKey", "inactive-key", not_found_raise_exception=False
        )
        self.assertEqual(
            exc_info.exception.detail,
            "API key is inactive. Please contact an admin.",
        )

    def test_get_api_key_header_returns_ok_response_when_api_key_is_active(self):
        api_key_in_db = MagicMock(active=True)
        repository = MagicMock()
        repository.read_by_column.return_value = api_key_in_db

        with patch.object(
            Container, "apikey_repository", MagicMock(return_value=repository)
        ):
            response = ApiKeyService.get_api_key_header("valid-key")

        repository.read_by_column.assert_called_once_with(
            "apiKey", "valid-key", not_found_raise_exception=False
        )
        self.assertTrue(response.sucess)
        self.assertEqual(response.data, api_key_in_db)


if __name__ == "__main__":
    unittest.main()
