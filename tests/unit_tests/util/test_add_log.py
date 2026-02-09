import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schema.logs_schema import CreateLogs
from app.schema.oauth_users_schema import CreateOAuthUser
from app.util.add_log import add_log


class TestAddLog(unittest.IsolatedAsyncioTestCase):
    async def test_add_log_success_with_api_key_and_oauth_user(self):
        service_log = MagicMock()
        service_log.add = AsyncMock(return_value=None)

        result = await add_log(
            module="games",
            log_level="INFO",
            message="test message",
            details={"k": "v"},
            service_log=service_log,
            api_key="api-key-1",
            oauth_user_id="oauth-user-1",
        )

        self.assertIsNone(result)
        service_log.add.assert_awaited_once()

        log_entry = service_log.add.await_args.args[0]
        self.assertIsInstance(log_entry, CreateLogs)
        self.assertEqual(log_entry.module, "games")
        self.assertEqual(log_entry.log_level, "INFO")
        self.assertEqual(log_entry.message, "test message")
        self.assertEqual(log_entry.details, {"k": "v"})
        self.assertEqual(log_entry.apiKey_used, "api-key-1")
        self.assertEqual(log_entry.oauth_user_id, "oauth-user-1")

    async def test_add_log_success_without_optional_identifiers(self):
        service_log = MagicMock()
        service_log.add = AsyncMock(return_value=None)

        await add_log(
            module="users",
            log_level="WARNING",
            message="no ids",
            details={},
            service_log=service_log,
        )

        service_log.add.assert_awaited_once()
        log_entry = service_log.add.await_args.args[0]
        self.assertIsInstance(log_entry, CreateLogs)
        self.assertIsNone(log_entry.apiKey_used)
        self.assertIsNone(log_entry.oauth_user_id)

    @patch("app.util.add_log.Container.oauth_users_service")
    @patch("builtins.print")
    async def test_add_log_retries_after_failure_and_creates_oauth_user(
        self, mock_print, mock_oauth_users_service
    ):
        service_log = MagicMock()
        service_log.add = AsyncMock(side_effect=[Exception("db error"), None])

        oauthusers_service = MagicMock()
        oauthusers_service.add = AsyncMock(return_value=None)
        mock_oauth_users_service.return_value = oauthusers_service

        retry_coroutine = await add_log(
            module="apikey",
            log_level="ERROR",
            message="failing path",
            details={"error": "db"},
            service_log=service_log,
            api_key="api-key-2",
            oauth_user_id="oauth-user-2",
        )

        self.assertTrue(asyncio.iscoroutine(retry_coroutine))
        self.assertEqual(service_log.add.await_count, 1)
        mock_oauth_users_service.assert_called_once()
        oauthusers_service.add.assert_awaited_once()
        created_oauth_user = oauthusers_service.add.await_args.args[0]
        self.assertIsInstance(created_oauth_user, CreateOAuthUser)
        self.assertEqual(created_oauth_user.provider, "keycloak")
        self.assertEqual(created_oauth_user.provider_user_id, "oauth-user-2")
        self.assertEqual(created_oauth_user.status, "active")
        mock_print.assert_called_once()
        self.assertIn("Error adding log", mock_print.call_args.args[0])

        retry_result = await retry_coroutine
        self.assertIsNone(retry_result)
        self.assertEqual(service_log.add.await_count, 2)


if __name__ == "__main__":
    unittest.main()
