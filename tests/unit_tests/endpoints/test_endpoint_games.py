import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.api.v1.endpoints import games
from app.core.exceptions import ForbiddenError, InternalServerError
from app.schema.games_schema import PatchGame, PostCreateGame, PostFindGame
from app.schema.task_schema import (AddActionDidByUserInTask,
                                    AsignPointsToExternalUserId, CreateTaskPost,
                                    CreateTasksPost, PostFindTask)
from app.schema.tasks_params_schema import CreateTaskParams


class _SchemaWithoutSimulated:
    def __init__(self, external_user_id):
        self.externalUserId = external_user_id
        self.data = {"points": 1}

    def dict(self):
        return {"externalUserId": self.externalUserId, "data": self.data}


class TestGamesEndpoints(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._patch_add_log = patch(
            "app.api.v1.endpoints.games.add_log",
            new=AsyncMock(),
        )
        self._patch_valid_access_token = patch(
            "app.api.v1.endpoints.games.valid_access_token",
            new=AsyncMock(return_value=SimpleNamespace(data={"sub": "oauth-user-1"})),
        )
        self._patch_check_role = patch(
            "app.api.v1.endpoints.games.check_role",
            return_value=False,
        )
        self._patch_hash = patch(
            "app.api.v1.endpoints.games.calculate_hash_simulated_strategy",
            return_value="sim-hash-1",
        )
        self._patch_secret = patch.object(games.configs, "SECRET_KEY", "test-secret")

        self.mock_add_log = self._patch_add_log.start()
        self.mock_valid_access_token = self._patch_valid_access_token.start()
        self.mock_check_role = self._patch_check_role.start()
        self.mock_hash = self._patch_hash.start()
        self._patch_secret.start()

    def tearDown(self):
        patch.stopall()

    @staticmethod
    def _api_key_header(api_key="api-key-1"):
        return SimpleNamespace(data=SimpleNamespace(apiKey=api_key))

    @staticmethod
    def _oauth_service(user_exists=True, async_add=True):
        service_oauth = MagicMock()
        service_oauth.get_user_by_sub.return_value = (
            SimpleNamespace(id="oauth-user") if user_exists else None
        )
        service_oauth.add = AsyncMock() if async_add else MagicMock()
        return service_oauth

    async def test_get_games_list_without_token_uses_api_key_filter(self):
        schema = PostFindGame(ordering="-created_at", page=1, page_size=10)
        service = MagicMock()
        service.get_all_games.return_value = {"items": []}

        result = await games.get_games_list(
            schema=schema,
            service=service,
            service_log=MagicMock(),
            service_oauth=self._oauth_service(),
            token=None,
            api_key_header=self._api_key_header("k-1"),
        )

        self.assertEqual(result, {"items": []})
        service.get_all_games.assert_called_once_with(schema, "k-1")

    async def test_get_games_list_with_admin_token_returns_unfiltered(self):
        self.mock_check_role.return_value = True
        schema = PostFindGame(ordering="-created_at", page=1, page_size=10)
        service = MagicMock()
        service.get_all_games.return_value = {"items": ["all"]}
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.get_games_list(
            schema=schema,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header("k-2"),
        )

        self.assertEqual(result, {"items": ["all"]})
        service.get_all_games.assert_called_once_with(schema)
        service_oauth.add.assert_awaited_once()

    async def test_get_game_by_id_with_token(self):
        game_id = uuid4()
        service = MagicMock()
        expected = {"id": str(game_id)}
        service.get_by_gameId.return_value = expected
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.get_game_by_id(
            gameId=game_id,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, expected)
        service.get_by_gameId.assert_called_once_with(game_id)
        service_oauth.add.assert_awaited_once()

    async def test_delete_game_by_id_success(self):
        game_id = uuid4()
        service = MagicMock()
        service.delete_game_by_id.return_value = {"gameId": str(game_id)}
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.delete_game_by_id(
            gameId=game_id,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"gameId": str(game_id)})
        service.delete_game_by_id.assert_called_once_with(game_id)

    async def test_delete_game_by_id_error_logs_and_raises(self):
        game_id = uuid4()
        service = MagicMock()
        service.delete_game_by_id.side_effect = RuntimeError("delete failed")

        with self.assertRaises(RuntimeError):
            await games.delete_game_by_id(
                gameId=game_id,
                service=service,
                service_log=MagicMock(),
                service_oauth=self._oauth_service(),
                token=None,
                api_key_header=self._api_key_header(),
            )

    async def test_create_game_success(self):
        schema = PostCreateGame(
            externalGameId="game_slug_1",
            platform="web",
            strategyId="default",
            params=[],
            apiKey_used=None,
            oauth_user_id=None,
        )
        service = MagicMock()
        service.create = AsyncMock(return_value=SimpleNamespace(gameId=uuid4()))
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        response = await games.create_game(
            schema=schema,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header("k-3"),
        )

        self.assertTrue(hasattr(response, "gameId"))
        service.create.assert_awaited_once()
        service_oauth.add.assert_awaited_once()

    async def test_create_game_error_logs_and_raises(self):
        schema = PostCreateGame(
            externalGameId="game_slug_2",
            platform="web",
            strategyId="default",
            params=[],
            apiKey_used=None,
            oauth_user_id=None,
        )
        service = MagicMock()
        service.create = AsyncMock(side_effect=RuntimeError("create failed"))

        with self.assertRaises(RuntimeError):
            await games.create_game(
                schema=schema,
                service=service,
                service_log=MagicMock(),
                service_oauth=self._oauth_service(),
                token=None,
                api_key_header=self._api_key_header(),
            )

    async def test_patch_game_success(self):
        game_id = uuid4()
        schema = PatchGame(externalGameId="slug", strategyId="default", platform="web")
        service = MagicMock()
        service.patch_game_by_id = AsyncMock(return_value={"ok": True})
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.patch_game(
            gameId=game_id,
            schema=schema,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"ok": True})
        service.patch_game_by_id.assert_awaited_once_with(game_id, schema)
        service_oauth.add.assert_awaited_once()

    async def test_patch_game_error_logs_and_raises(self):
        game_id = uuid4()
        schema = PatchGame(externalGameId="slug", strategyId="default", platform="web")
        service = MagicMock()
        service.patch_game_by_id = AsyncMock(side_effect=RuntimeError("patch failed"))

        with self.assertRaises(RuntimeError):
            await games.patch_game(
                gameId=game_id,
                schema=schema,
                service=service,
                service_log=MagicMock(),
                service_oauth=self._oauth_service(),
                token=None,
                api_key_header=self._api_key_header(),
            )

    async def test_get_strategy_by_game_id(self):
        game_id = uuid4()
        service = MagicMock()
        service.get_strategy_by_gameId.return_value = {"id": "default"}
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.get_strategy_by_gameId(
            gameId=game_id,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"id": "default"})
        service.get_strategy_by_gameId.assert_called_once_with(game_id)

    async def test_create_task_success(self):
        game_id = uuid4()
        create_query = CreateTaskPost(
            externalTaskId="task-1",
            strategyId="default",
            params=[CreateTaskParams(key="k", value=1)],
        )
        service = MagicMock()
        service.create_task_by_game_id = AsyncMock(return_value={"task": "created"})
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.create_task(
            gameId=game_id,
            create_query=create_query,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"task": "created"})
        service.create_task_by_game_id.assert_awaited_once_with(
            game_id, create_query, "api-key-1"
        )

    async def test_create_task_error_logs_and_raises(self):
        game_id = uuid4()
        create_query = CreateTaskPost(
            externalTaskId="task-2", strategyId=None, params=None
        )
        service = MagicMock()
        service.create_task_by_game_id = AsyncMock(
            side_effect=RuntimeError("task failed")
        )

        with self.assertRaises(RuntimeError):
            await games.create_task(
                gameId=game_id,
                create_query=create_query,
                service=service,
                service_log=MagicMock(),
                service_oauth=self._oauth_service(),
                token=None,
                api_key_header=self._api_key_header(),
            )

    async def test_create_tasks_bulk_with_success_and_failure(self):
        game_id = uuid4()
        bulk_query = CreateTasksPost(
            tasks=[
                CreateTaskPost(
                    externalTaskId="task-1", strategyId="default", params=None
                ),
                CreateTaskPost(
                    externalTaskId="task-2", strategyId="default", params=None
                ),
            ]
        )
        service = MagicMock()
        service.create_task_by_game_id = AsyncMock(
            side_effect=[{"task": "task-1"}, RuntimeError("bulk error")]
        )
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.create_tasks_bulk(
            gameId=game_id,
            create_query=bulk_query,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(len(result["succesfully_created"]), 1)
        self.assertEqual(len(result["failed_to_create"]), 1)
        self.assertEqual(result["failed_to_create"][0]["error"], "bulk error")

    async def test_get_task_list(self):
        game_id = uuid4()
        find_query = PostFindTask(ordering="-created_at", page=1, page_size=10)
        service = MagicMock()
        service.get_tasks_list_by_gameId.return_value = {"items": []}
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.get_task_list(
            gameId=game_id,
            find_query=find_query,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"items": []})
        service.get_tasks_list_by_gameId.assert_called_once_with(game_id, find_query)

    async def test_get_task_by_game_id_task_id(self):
        game_id = uuid4()
        service = MagicMock()
        service.get_task_by_externalGameId_externalTaskId.return_value = {"task": "one"}
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.get_task_by_gameId_taskId(
            gameId=game_id,
            externalTaskId="task-1",
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"task": "one"})
        service.get_task_by_externalGameId_externalTaskId.assert_called_once_with(
            str(game_id), "task-1"
        )

    async def test_get_points_by_game_id(self):
        game_id = uuid4()
        service = MagicMock()
        service.get_points_by_gameId.return_value = {"game": "points"}
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.get_points_by_gameId(
            gameId=game_id,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"game": "points"})

    async def test_get_points_by_game_id_with_details(self):
        game_id = uuid4()
        service = MagicMock()
        service.get_points_by_gameId_with_details.return_value = {"game": "details"}
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.get_points_by_gameId_with_details(
            gameId=game_id,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"game": "details"})

    async def test_get_points_of_user_in_game(self):
        game_id = uuid4()
        service = MagicMock()
        service.get_points_of_user_in_game.return_value = [{"externalUserId": "u1"}]
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.get_points_of_user_in_game(
            gameId=game_id,
            externalUserId="u1",
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, [{"externalUserId": "u1"}])

    async def test_get_points_simulated_raises_when_secret_missing(self):
        with patch.object(games.configs, "SECRET_KEY", None):
            with self.assertRaises(InternalServerError):
                await games.get_points_simulated_of_user_in_game(
                    gameId=uuid4(),
                    externalUserId="u1",
                    service=MagicMock(),
                    service_log=MagicMock(),
                    service_user=MagicMock(),
                    service_oauth=self._oauth_service(async_add=False),
                    token="Bearer any",
                )

    async def test_get_points_simulated_raises_forbidden_when_admin_and_other_user(
        self,
    ):
        self.mock_check_role.return_value = True
        self.mock_valid_access_token.return_value = SimpleNamespace(
            data={"sub": "oauth-user-1"}
        )

        with self.assertRaises(ForbiddenError):
            await games.get_points_simulated_of_user_in_game(
                gameId=uuid4(),
                externalUserId="different-user",
                service=MagicMock(),
                service_log=MagicMock(),
                service_user=MagicMock(),
                service_oauth=self._oauth_service(async_add=False),
                token="Bearer any",
            )

    async def test_get_points_simulated_success(self):
        game_id = uuid4()
        simulated_tasks = [
            {
                "externalUserId": "oauth-user-1",
                "externalTaskId": "task-1",
                "userGroup": "random_range",
                "dimensions": [],
                "totalSimulatedPoints": 10,
                "expirationDate": "2026-02-10T00:00:00",
            }
        ]
        service = MagicMock()
        service.get_points_simulated_of_user_in_game = AsyncMock(
            return_value=(simulated_tasks, "external-game-1")
        )
        service_oauth = self._oauth_service(user_exists=False, async_add=False)

        result = await games.get_points_simulated_of_user_in_game(
            gameId=game_id,
            externalUserId="oauth-user-1",
            service=service,
            service_log=MagicMock(),
            service_user=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
        )

        self.assertEqual(result.simulationHash, "sim-hash-1")
        self.assertEqual(len(result.tasks), 1)
        service.get_points_simulated_of_user_in_game.assert_awaited_once()
        service_oauth.add.assert_called_once()

    async def test_user_action_in_task(self):
        game_id = uuid4()
        schema = AddActionDidByUserInTask(
            typeAction="click",
            data={"x": 1},
            description="desc",
            externalUserId="u1",
        )
        service = MagicMock()
        service.user_add_action_in_task = AsyncMock(return_value={"ok": True})
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.user_action_in_task(
            gameId=game_id,
            externalTaskId="task-1",
            schema=schema,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"ok": True})
        service.user_add_action_in_task.assert_awaited_once_with(
            game_id, "task-1", schema, "api-key-1"
        )

    async def test_assign_points_to_user_with_simulated_flag(self):
        game_id = uuid4()
        schema = AsignPointsToExternalUserId(
            externalUserId="u1",
            data={"points": 1},
            isSimulated=True,
        )
        service = MagicMock()
        service.assign_points_to_user = AsyncMock(return_value={"points": 1})
        service_oauth = self._oauth_service(user_exists=False, async_add=True)

        result = await games.assign_points_to_user(
            gameId=game_id,
            externalTaskId="task-1",
            schema=schema,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"points": 1})
        service.assign_points_to_user.assert_awaited_once_with(
            game_id, "task-1", schema, True, "api-key-1"
        )

    async def test_assign_points_to_user_defaults_simulated_flag_to_false(self):
        game_id = uuid4()
        schema = _SchemaWithoutSimulated("u2")
        service = MagicMock()
        service.assign_points_to_user = AsyncMock(return_value={"points": 2})

        result = await games.assign_points_to_user(
            gameId=game_id,
            externalTaskId="task-2",
            schema=schema,
            service=service,
            service_log=MagicMock(),
            service_oauth=self._oauth_service(),
            token=None,
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"points": 2})
        service.assign_points_to_user.assert_awaited_once_with(
            game_id, "task-2", schema, False, "api-key-1"
        )

    async def test_get_points_by_task_id(self):
        service = MagicMock()
        service.get_points_by_task_id.return_value = [{"externalUserId": "u1"}]
        service_oauth = self._oauth_service(user_exists=False, async_add=True)
        game_id = uuid4()

        result = await games.get_points_by_task_id(
            gameId=game_id,
            externalTaskId="task-1",
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, [{"externalUserId": "u1"}])

    async def test_get_points_of_user_by_task_id(self):
        service = MagicMock()
        service.get_points_of_user_by_task_id.return_value = {"externalUserId": "u1"}
        service_oauth = self._oauth_service(user_exists=False, async_add=True)
        game_id = uuid4()

        result = await games.get_points_of_user_by_task_id(
            gameId=game_id,
            externalTaskId="task-1",
            externalUserId="u1",
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, {"externalUserId": "u1"})

    async def test_get_points_by_task_id_with_details(self):
        service = MagicMock()
        service.get_points_by_task_id_with_details.return_value = [{"details": True}]
        service_oauth = self._oauth_service(user_exists=False, async_add=True)
        game_id = uuid4()

        result = await games.get_points_by_task_id_with_details(
            gameId=game_id,
            externalTaskId="task-1",
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertEqual(result, [{"details": True}])

    async def test_get_users_by_game_id(self):
        service = MagicMock()
        service.get_users_by_gameId.return_value = {
            "gameId": str(uuid4()),
            "tasks": [],
        }
        service_oauth = self._oauth_service(user_exists=False, async_add=True)
        game_id = uuid4()

        result = await games.get_users_by_gameId(
            gameId=game_id,
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer any",
            api_key_header=self._api_key_header(),
        )

        self.assertIn("tasks", result)


if __name__ == "__main__":
    unittest.main()
