import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.v1.endpoints import users
from app.schema.user_actions_schema import CreateUserBodyActions
from app.schema.user_schema import (PostAssignPointsToUserWithCaseName,
                                    PostPointsConversionRequest)


class TestUsersEndpoints(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._patch_add_log = patch(
            "app.api.v1.endpoints.users.add_log",
            new=AsyncMock(),
        )
        self._patch_valid_access_token = patch(
            "app.api.v1.endpoints.users.valid_access_token",
            new=AsyncMock(return_value=SimpleNamespace(data={"sub": "oauth-user-1"})),
        )

        self.mock_add_log = self._patch_add_log.start()
        self.mock_valid_access_token = self._patch_valid_access_token.start()

    def tearDown(self):
        patch.stopall()

    @staticmethod
    def _api_key_header(api_key="api-key-1"):
        return SimpleNamespace(data=SimpleNamespace(apiKey=api_key))

    @staticmethod
    def _oauth_service(user_exists=True):
        service_oauth = MagicMock()
        service_oauth.get_user_by_sub.return_value = (
            SimpleNamespace(id="oauth-user") if user_exists else None
        )
        service_oauth.add = AsyncMock()
        return service_oauth

    async def test_query_user_points_success_with_token_and_new_oauth_user(self):
        service = MagicMock()
        expected = [
            {"externalUserId": "u1", "points": 10, "timesAwarded": 1, "games": []}
        ]
        service.get_points_by_user_list.return_value = expected
        service_oauth = self._oauth_service(user_exists=False)

        result = await users.query_user_points(
            schema=["u1"],
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header("k-1"),
        )

        self.assertEqual(result, expected)
        service.get_points_by_user_list.assert_called_once_with(["u1"])
        service_oauth.add.assert_awaited_once()
        self.assertGreaterEqual(self.mock_add_log.await_count, 2)

    async def test_query_user_points_error_logs_and_raises(self):
        service = MagicMock()
        service.get_points_by_user_list.side_effect = RuntimeError("query failed")

        with self.assertRaises(RuntimeError):
            await users.query_user_points(
                schema=["u1"],
                service=service,
                service_log=MagicMock(),
                service_oauth=self._oauth_service(),
                token=None,
                api_key_header=self._api_key_header(),
            )

    async def test_get_points_by_user_id_success_with_token_and_new_oauth_user(self):
        service = MagicMock()
        expected = [{"externalGameId": "g1", "created_at": "now", "task": []}]
        service.get_points_by_externalUserId.return_value = expected
        service_oauth = self._oauth_service(user_exists=False)

        result = await users.get_points_by_user_id(
            externalUserId="u1",
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, expected)
        service.get_points_by_externalUserId.assert_called_once_with("u1")
        service_oauth.add.assert_awaited_once()

    async def test_get_points_by_user_id_error_logs_and_raises(self):
        service = MagicMock()
        service.get_points_by_externalUserId.side_effect = RuntimeError(
            "get points failed"
        )

        with self.assertRaises(RuntimeError):
            await users.get_points_by_user_id(
                externalUserId="u1",
                service=service,
                service_log=MagicMock(),
                service_oauth=self._oauth_service(),
                token=None,
                api_key_header=self._api_key_header(),
            )

    async def test_get_wallet_by_user_id_success_with_token_and_new_oauth_user(self):
        service = MagicMock()
        expected = {"userId": "u1", "wallet": None, "walletTransactions": []}
        service.get_wallet_by_externalUserId = AsyncMock(return_value=expected)
        service_oauth = self._oauth_service(user_exists=False)

        result = await users.get_wallet_by_user_id(
            externalUserId="u1",
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, expected)
        service.get_wallet_by_externalUserId.assert_awaited_once_with("u1")
        service_oauth.add.assert_awaited_once()

    async def test_get_wallet_by_user_id_error_logs_and_raises(self):
        service = MagicMock()
        service.get_wallet_by_externalUserId = AsyncMock(
            side_effect=RuntimeError("wallet failed")
        )

        with self.assertRaises(RuntimeError):
            await users.get_wallet_by_user_id(
                externalUserId="u1",
                service=service,
                service_log=MagicMock(),
                service_oauth=self._oauth_service(),
                token=None,
                api_key_header=self._api_key_header(),
            )

    async def test_assign_points_by_external_user_id_success(self):
        schema = PostAssignPointsToUserWithCaseName(
            taskId="task-ext-1",
            caseName="CaseA",
            points=30,
            description="reward",
            data={"source": "mobile"},
        )
        service = MagicMock()
        service.task_repository = MagicMock()
        service.user_repository = MagicMock()
        service.task_repository.read_by_column.return_value = SimpleNamespace(
            id="task-id-1"
        )
        service.user_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1"
        )
        service.assign_points_to_user = AsyncMock(return_value={"ok": True})
        service_oauth = self._oauth_service(user_exists=False)

        result = await users.assign_points_by_external_user_id(
            externalUserId="ext-user-1",
            schema=schema,
            service=service,
            service_oauth=service_oauth,
            service_log=MagicMock(),
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"ok": True})
        service.task_repository.read_by_column.assert_called_once()
        service.user_repository.read_by_column.assert_called_once()
        service.assign_points_to_user.assert_awaited_once()
        call_args = service.assign_points_to_user.await_args.args
        self.assertEqual(call_args[0], "user-id-1")
        self.assertEqual(call_args[1].userId, "user-id-1")
        self.assertEqual(call_args[1].taskId, "task-id-1")
        self.assertEqual(call_args[1].points, 30)
        self.assertEqual(call_args[2], "api-key-1")
        service_oauth.add.assert_awaited_once()

    async def test_assign_points_by_external_user_id_error_logs_and_raises(self):
        schema = PostAssignPointsToUserWithCaseName(
            taskId="task-ext-1",
            caseName="CaseA",
            points=30,
            description="reward",
            data=None,
        )
        service = MagicMock()
        service.task_repository = MagicMock()
        service.user_repository = MagicMock()
        service.task_repository.read_by_column.side_effect = RuntimeError(
            "task not found"
        )
        service.assign_points_to_user = AsyncMock()

        with self.assertRaises(RuntimeError):
            await users.assign_points_by_external_user_id(
                externalUserId="ext-user-1",
                schema=schema,
                service=service,
                service_oauth=self._oauth_service(),
                service_log=MagicMock(),
                token=None,
                api_key_header=self._api_key_header(),
            )

    async def test_preview_points_to_coins_conversion_success(self):
        service = MagicMock()
        expected = {
            "points": 100,
            "conversionRate": 0.1,
            "conversionRateDate": "2026-02-09",
            "convertedAmount": 10.0,
            "convertedCurrency": "coin",
            "haveEnoughPoints": True,
        }
        service.preview_points_to_coins_conversion_externalUserId.return_value = (
            expected
        )
        service_oauth = self._oauth_service(user_exists=False)

        result = await users.preview_points_to_coins_conversion(
            externalUserId="u1",
            points=100,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, expected)
        service.preview_points_to_coins_conversion_externalUserId.assert_called_once_with(
            "u1", 100
        )
        service_oauth.add.assert_awaited_once()

    async def test_preview_points_to_coins_conversion_error_logs_and_raises(self):
        service = MagicMock()
        service.preview_points_to_coins_conversion_externalUserId.side_effect = (
            RuntimeError("preview failed")
        )

        with self.assertRaises(RuntimeError):
            await users.preview_points_to_coins_conversion(
                externalUserId="u1",
                points=100,
                service=service,
                service_log=MagicMock(),
                service_oauth=self._oauth_service(),
                token=None,
                api_key_header=self._api_key_header(),
            )

    async def test_convert_points_to_coins_success(self):
        schema = PostPointsConversionRequest(points=25)
        service = MagicMock()
        expected = {
            "transactionId": "tx-1",
            "points": 25,
            "conversionRate": 0.2,
            "conversionRateDate": "2026-02-09",
            "convertedAmount": 5.0,
            "convertedCurrency": "coin",
            "haveEnoughPoints": True,
        }
        service.convert_points_to_coins_externalUserId = AsyncMock(
            return_value=expected
        )
        service_oauth = self._oauth_service(user_exists=False)

        result = await users.convert_points_to_coins(
            externalUserId="u1",
            schema=schema,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header("k-2"),
        )

        self.assertEqual(result, expected)
        service.convert_points_to_coins_externalUserId.assert_awaited_once_with(
            "u1", schema, "k-2"
        )
        service_oauth.add.assert_awaited_once()

    async def test_convert_points_to_coins_error_logs_and_raises(self):
        schema = PostPointsConversionRequest(points=25)
        service = MagicMock()
        service.convert_points_to_coins_externalUserId = AsyncMock(
            side_effect=RuntimeError("convert failed")
        )

        with self.assertRaises(RuntimeError):
            await users.convert_points_to_coins(
                externalUserId="u1",
                schema=schema,
                service=service,
                service_log=MagicMock(),
                service_oauth=self._oauth_service(),
                token=None,
                api_key_header=self._api_key_header(),
            )

    async def test_add_action_to_user_success(self):
        schema = CreateUserBodyActions(
            typeAction="open_app",
            data={"screen": "home"},
            description="User opened app",
            apiKey_used=None,
        )
        service = MagicMock()
        expected = {
            "typeAction": "open_app",
            "description": "User opened app",
            "userId": "u1",
            "is_user_created": False,
            "message": "Action added successfully",
        }
        service.user_add_action_default = AsyncMock(return_value=expected)
        service_oauth = self._oauth_service(user_exists=False)

        result = await users.add_action_to_user(
            externalUserId="u1",
            schema=schema,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header("k-3"),
        )

        self.assertEqual(result, expected)
        service.user_add_action_default.assert_awaited_once_with("u1", schema, "k-3")
        service_oauth.add.assert_awaited_once()

    async def test_add_action_to_user_error_logs_and_raises(self):
        schema = CreateUserBodyActions(
            typeAction="open_app",
            data={"screen": "home"},
            description="User opened app",
            apiKey_used=None,
        )
        service = MagicMock()
        service.user_add_action_default = AsyncMock(
            side_effect=RuntimeError("action failed")
        )

        with self.assertRaises(RuntimeError):
            await users.add_action_to_user(
                externalUserId="u1",
                schema=schema,
                service=service,
                service_log=MagicMock(),
                service_oauth=self._oauth_service(),
                token=None,
                api_key_header=self._api_key_header(),
            )


if __name__ == "__main__":
    unittest.main()
