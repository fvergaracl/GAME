import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import jwt
from fastapi import HTTPException

from app.api.v1.endpoints import games
from app.core.exceptions import (
    DuplicatedError,
    ForbiddenError,
    InternalServerError,
    PreconditionFailedError,
    TooManyRequestsError,
)
from app.middlewares.auth_context import AuditLogger, AuthContext
from app.schema.games_schema import PatchGame, PostCreateGame, PostFindGame
from app.schema.task_schema import (
    AddActionDidByUserInTask,
    AsignPointsToExternalUserId,
    CreateTaskPost,
    CreateTasksPost,
    PostFindTask,
)
from app.schema.tasks_params_schema import CreateTaskParams


class _SchemaWithoutSimulated:
    def __init__(self, external_user_id):
        self.externalUserId = external_user_id
        self.data = {"points": 1}

    def model_dump(self):
        return {"externalUserId": self.externalUserId, "data": self.data}


_GAMES_SUBMODULES = (
    "app.api.v1.endpoints.games_crud",
    "app.api.v1.endpoints.games_strategy",
    "app.api.v1.endpoints.games_tasks",
    "app.api.v1.endpoints.games_points",
    "app.api.v1.endpoints.games_users",
)


def _patch_in_submodules(name, **kwargs):
    """Patch ``name`` across every games_* sub-module that imports it.

    The endpoint code was split into sub-resource files, so test patches must
    target each sub-module instead of the old monolithic ``games`` module.
    Sub-modules that don't bind ``name`` are skipped silently.
    """
    patches = []
    for mod in _GAMES_SUBMODULES:
        try:
            patches.append(patch(f"{mod}.{name}", **kwargs))
        except AttributeError:
            continue
    return patches


class TestGamesEndpoints(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_add_log = AsyncMock()
        self.mock_hash = MagicMock(return_value="sim-hash-1")

        self._patches = [
            patch("app.middlewares.auth_context.add_log", new=self.mock_add_log)
        ]
        self._patches.append(
            patch(
                "app.api.v1.endpoints.games_points.calculate_hash_simulated_strategy",
                new=self.mock_hash,
            )
        )
        self._patches.append(patch.object(games.configs, "SECRET_KEY", "test-secret"))

        for p in self._patches:
            p.start()

    def tearDown(self):
        patch.stopall()

    def test_extract_oauth_user_id_from_token_returns_sub(self):
        token = jwt.encode(
            {"sub": "oauth-user-1"},
            "unit-test-secret-key-with-32-chars",
            algorithm="HS256",
        )
        self.assertEqual(games._extract_oauth_user_id_from_token(token), "oauth-user-1")

    def test_extract_oauth_user_id_from_token_returns_none_for_invalid_token(self):
        self.assertIsNone(games._extract_oauth_user_id_from_token("not-a-jwt"))

    @staticmethod
    def _api_key_header(api_key="api-key-1"):
        return SimpleNamespace(data=SimpleNamespace(apiKey=api_key))

    @staticmethod
    def _scope_kwargs(
        api_key="api-key-1", oauth_user_id="oauth-user-1", is_admin=False
    ):
        return {
            "api_key": api_key,
            "oauth_user_id": oauth_user_id,
            "is_admin": is_admin,
            "enforce_scope": True,
        }

    @staticmethod
    def _audit(api_key="api-key-1", oauth_user_id=None, is_admin=False):
        return AuditLogger(
            "game",
            MagicMock(),
            AuthContext(
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
                token_data={"sub": oauth_user_id} if oauth_user_id else None,
            ),
        )

    @classmethod
    def _audit_from_header(cls, api_key_header, oauth_user_id=None, is_admin=False):
        api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
        return cls._audit(
            api_key=api_key, oauth_user_id=oauth_user_id, is_admin=is_admin
        )

    @staticmethod
    def _oauth_service(user_exists=True, async_add=True):
        service_oauth = MagicMock()
        service_oauth.get_user_by_sub = AsyncMock(
            return_value=SimpleNamespace(id="oauth-user") if user_exists else None
        )
        service_oauth.add = AsyncMock() if async_add else MagicMock()
        return service_oauth

    @staticmethod
    def _request(host="198.51.100.1", forwarded_for=None):
        headers = {}
        if forwarded_for:
            headers["X-Forwarded-For"] = forwarded_for
        return SimpleNamespace(headers=headers, client=SimpleNamespace(host=host))

    @staticmethod
    def _abuse_service(ip="198.51.100.1", enforce_side_effect=None):
        service = AsyncMock()
        service.extract_client_ip = MagicMock(return_value=ip)
        service.enforce_task_mutation_limits = AsyncMock(
            side_effect=enforce_side_effect
        )
        return service

    async def test_get_games_list_without_token_uses_api_key_filter(self):
        schema = PostFindGame(ordering="-created_at", page=1, page_size=10)
        service = AsyncMock()
        service.get_all_games.return_value = {"items": []}

        result = await games.get_games_list(
            schema=schema,
            service=service,
            audit=self._audit(api_key="k-1", oauth_user_id=None),
        )

        self.assertEqual(result, {"items": []})
        service.get_all_games.assert_called_once_with(
            schema,
            api_key="k-1",
            oauth_user_id=None,
            is_admin=False,
        )

    async def test_get_games_list_with_admin_token_returns_unfiltered(self):
        schema = PostFindGame(ordering="-created_at", page=1, page_size=10)
        service = AsyncMock()
        service.get_all_games.return_value = {"items": ["all"]}

        result = await games.get_games_list(
            schema=schema,
            service=service,
            audit=self._audit(
                api_key="k-2", oauth_user_id="oauth-user-1", is_admin=True
            ),
        )

        self.assertEqual(result, {"items": ["all"]})
        service.get_all_games.assert_called_once_with(
            schema,
            api_key="k-2",
            oauth_user_id="oauth-user-1",
            is_admin=True,
        )

    async def test_get_game_by_id_with_token(self):
        game_id = uuid4()
        service = AsyncMock()
        expected = {"id": str(game_id)}
        service.get_by_gameId.return_value = expected

        result = await games.get_game_by_id(
            gameId=game_id,
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, expected)
        service.get_by_gameId.assert_called_once_with(
            game_id,
            **self._scope_kwargs(),
        )

    async def test_delete_game_by_id_success(self):
        game_id = uuid4()
        service = AsyncMock()
        service.delete_game_by_id.return_value = {"gameId": str(game_id)}

        result = await games.delete_game_by_id(
            gameId=game_id,
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, {"gameId": str(game_id)})
        service.delete_game_by_id.assert_called_once_with(
            game_id,
            **self._scope_kwargs(),
        )

    async def test_delete_game_by_id_error_logs_and_raises(self):
        game_id = uuid4()
        service = AsyncMock()
        service.delete_game_by_id.side_effect = RuntimeError("delete failed")

        with self.assertRaises(RuntimeError):
            await games.delete_game_by_id(
                gameId=game_id,
                service=service,
                audit=self._audit(api_key="api-key-1", oauth_user_id=None),
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
        service = AsyncMock()
        service.create = AsyncMock(return_value=SimpleNamespace(gameId=uuid4()))

        response = await games.create_game(
            schema=schema,
            service=service,
            audit=self._audit(api_key="k-3", oauth_user_id="oauth-user-1"),
        )

        self.assertTrue(hasattr(response, "gameId"))
        service.create.assert_awaited_once()

    async def test_create_game_error_logs_and_raises(self):
        schema = PostCreateGame(
            externalGameId="game_slug_2",
            platform="web",
            strategyId="default",
            params=[],
            apiKey_used=None,
            oauth_user_id=None,
        )
        service = AsyncMock()
        service.create = AsyncMock(side_effect=RuntimeError("create failed"))

        with self.assertRaises(RuntimeError):
            await games.create_game(
                schema=schema,
                service=service,
                audit=self._audit(api_key="api-key-1", oauth_user_id=None),
            )

    async def test_patch_game_success(self):
        game_id = uuid4()
        schema = PatchGame(externalGameId="slug", strategyId="default", platform="web")
        service = AsyncMock()
        service.patch_game_by_id = AsyncMock(return_value={"ok": True})

        result = await games.patch_game(
            gameId=game_id,
            schema=schema,
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, {"ok": True})
        service.patch_game_by_id.assert_awaited_once_with(
            game_id,
            schema,
            **self._scope_kwargs(),
        )

    async def test_patch_game_error_logs_and_raises(self):
        game_id = uuid4()
        schema = PatchGame(externalGameId="slug", strategyId="default", platform="web")
        service = AsyncMock()
        service.patch_game_by_id = AsyncMock(side_effect=RuntimeError("patch failed"))

        with self.assertRaises(RuntimeError):
            await games.patch_game(
                gameId=game_id,
                schema=schema,
                service=service,
                audit=self._audit(api_key="api-key-1", oauth_user_id=None),
            )

    async def test_get_strategy_by_game_id(self):
        game_id = uuid4()
        service = AsyncMock()
        service.get_strategy_by_gameId.return_value = {"id": "default"}

        result = await games.get_strategy_by_gameId(
            gameId=game_id,
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, {"id": "default"})
        service.get_strategy_by_gameId.assert_called_once_with(
            game_id,
            **self._scope_kwargs(),
        )

    async def test_create_task_success(self):
        game_id = uuid4()
        create_query = CreateTaskPost(
            externalTaskId="task-1",
            strategyId="default",
            params=[CreateTaskParams(key="k", value=1)],
        )
        service = AsyncMock()
        service.create_task_by_game_id = AsyncMock(return_value={"task": "created"})

        result = await games.create_task(
            gameId=game_id,
            create_query=create_query,
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, {"task": "created"})
        service.create_task_by_game_id.assert_awaited_once_with(
            game_id,
            create_query,
            "api-key-1",
            oauth_user_id="oauth-user-1",
            is_admin=False,
            enforce_scope=True,
        )

    async def test_create_task_error_logs_and_raises(self):
        game_id = uuid4()
        create_query = CreateTaskPost(
            externalTaskId="task-2", strategyId=None, params=None
        )
        service = AsyncMock()
        service.create_task_by_game_id = AsyncMock(
            side_effect=RuntimeError("task failed")
        )

        with self.assertRaises(RuntimeError):
            await games.create_task(
                gameId=game_id,
                create_query=create_query,
                service=service,
                audit=self._audit(api_key="api-key-1", oauth_user_id=None),
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
        service = AsyncMock()
        service.create_task_by_game_id = AsyncMock(
            side_effect=[{"task": "task-1"}, RuntimeError("bulk error")]
        )

        result = await games.create_tasks_bulk(
            gameId=game_id,
            create_query=bulk_query,
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(len(result["succesfully_created"]), 1)
        self.assertEqual(len(result["failed_to_create"]), 1)
        self.assertEqual(result["failed_to_create"][0]["error"], "bulk error")

    async def test_get_task_list(self):
        game_id = uuid4()
        find_query = PostFindTask(ordering="-created_at", page=1, page_size=10)
        service = AsyncMock()
        service.get_tasks_list_by_gameId.return_value = {"items": []}

        result = await games.get_task_list(
            gameId=game_id,
            find_query=find_query,
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, {"items": []})
        service.get_tasks_list_by_gameId.assert_called_once_with(
            game_id,
            find_query,
            **self._scope_kwargs(),
        )

    async def test_get_task_by_game_id_task_id(self):
        game_id = uuid4()
        service = AsyncMock()
        service.get_task_by_externalGameId_externalTaskId.return_value = {"task": "one"}

        result = await games.get_task_by_gameId_taskId(
            gameId=game_id,
            externalTaskId="task-1",
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, {"task": "one"})
        service.get_task_by_externalGameId_externalTaskId.assert_called_once_with(
            str(game_id),
            "task-1",
            **self._scope_kwargs(),
        )

    async def test_get_points_by_game_id(self):
        game_id = uuid4()
        service = AsyncMock()
        service.get_points_by_gameId.return_value = {"game": "points"}

        result = await games.get_points_by_gameId(
            gameId=game_id,
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, {"game": "points"})

    async def test_get_points_by_game_id_with_details(self):
        game_id = uuid4()
        service = AsyncMock()
        service.get_points_by_gameId_with_details.return_value = {"game": "details"}

        result = await games.get_points_by_gameId_with_details(
            gameId=game_id,
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, {"game": "details"})

    async def test_get_points_of_user_in_game(self):
        game_id = uuid4()
        service = AsyncMock()
        service.get_points_of_user_in_game.return_value = [{"externalUserId": "u1"}]

        result = await games.get_points_of_user_in_game(
            gameId=game_id,
            externalUserId="u1",
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, [{"externalUserId": "u1"}])

    async def test_get_points_simulated_raises_when_secret_missing(self):
        with patch.object(games.configs, "SECRET_KEY", None):
            with self.assertRaises(InternalServerError):
                await games.get_points_simulated_of_user_in_game(
                    gameId=uuid4(),
                    externalUserId="u1",
                    service=MagicMock(),
                    audit=self._audit(api_key=None, oauth_user_id="oauth-user-1"),
                    service_user=MagicMock(),
                )

    async def test_get_points_simulated_raises_forbidden_when_admin_and_other_user(
        self,
    ):

        with self.assertRaises(ForbiddenError):
            await games.get_points_simulated_of_user_in_game(
                gameId=uuid4(),
                externalUserId="different-user",
                service=MagicMock(),
                audit=self._audit(
                    api_key=None, oauth_user_id="oauth-user-1", is_admin=True
                ),
                service_user=MagicMock(),
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
        service = AsyncMock()
        service.get_points_simulated_of_user_in_game = AsyncMock(
            return_value=(simulated_tasks, "external-game-1")
        )

        result = await games.get_points_simulated_of_user_in_game(
            gameId=game_id,
            externalUserId="oauth-user-1",
            service=service,
            audit=self._audit(api_key=None, oauth_user_id="oauth-user-1"),
            service_user=MagicMock(),
        )

        self.assertEqual(result.simulationHash, "sim-hash-1")
        self.assertEqual(len(result.tasks), 1)
        service.get_points_simulated_of_user_in_game.assert_awaited_once()

    async def test_user_action_in_task(self):
        game_id = uuid4()
        schema = AddActionDidByUserInTask(
            typeAction="click",
            data={"x": 1},
            description="desc",
            externalUserId="u1",
        )
        service = AsyncMock()
        service.user_add_action_in_task = AsyncMock(return_value={"ok": True})

        result = await games.user_action_in_task(
            gameId=game_id,
            externalTaskId="task-1",
            schema=schema,
            request=self._request(),
            service=service,
            abuse_prevention_service=self._abuse_service(),
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, {"ok": True})
        service.user_add_action_in_task.assert_awaited_once_with(
            game_id,
            "task-1",
            schema,
            "api-key-1",
            oauth_user_id="oauth-user-1",
            is_admin=False,
            enforce_scope=True,
        )

    async def test_user_action_in_task_with_invalid_bearer_does_not_crash_when_api_key_is_valid(
        self,
    ):
        game_id = uuid4()
        schema = AddActionDidByUserInTask(
            typeAction="click",
            data={"x": 1},
            description="desc",
            externalUserId="u1",
        )
        service = AsyncMock()
        service.user_add_action_in_task = AsyncMock(return_value={"ok": True})

        result = await games.user_action_in_task(
            gameId=game_id,
            externalTaskId="task-1",
            schema=schema,
            request=self._request(),
            service=service,
            abuse_prevention_service=self._abuse_service(),
            audit=self._audit(api_key="api-key-valid", oauth_user_id=None),
        )

        self.assertEqual(result, {"ok": True})

    async def test_assign_points_to_user_with_simulated_flag(self):
        game_id = uuid4()
        schema = AsignPointsToExternalUserId(
            externalUserId="u1",
            data={"points": 1},
            isSimulated=True,
        )
        service = AsyncMock()
        service.assign_points_to_user = AsyncMock(return_value={"points": 1})

        result = await games.assign_points_to_user(
            gameId=game_id,
            externalTaskId="task-1",
            schema=schema,
            request=self._request(),
            service=service,
            abuse_prevention_service=self._abuse_service(),
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, {"points": 1})
        service.assign_points_to_user.assert_awaited_once_with(
            game_id,
            "task-1",
            schema,
            True,
            "api-key-1",
            oauth_user_id="oauth-user-1",
            is_admin=False,
            enforce_scope=True,
        )

    async def test_assign_points_to_user_with_invalid_bearer_does_not_crash_when_api_key_is_valid(
        self,
    ):
        game_id = uuid4()
        schema = AsignPointsToExternalUserId(
            externalUserId="u1",
            data={"points": 1},
            isSimulated=False,
        )
        service = AsyncMock()
        service.assign_points_to_user = AsyncMock(return_value={"points": 1})

        result = await games.assign_points_to_user(
            gameId=game_id,
            externalTaskId="task-1",
            schema=schema,
            request=self._request(),
            service=service,
            abuse_prevention_service=self._abuse_service(),
            audit=self._audit(api_key="api-key-valid", oauth_user_id=None),
        )

        self.assertEqual(result, {"points": 1})

    async def test_assign_points_to_user_defaults_simulated_flag_to_false(self):
        game_id = uuid4()
        schema = _SchemaWithoutSimulated("u2")
        service = AsyncMock()
        service.assign_points_to_user = AsyncMock(return_value={"points": 2})

        result = await games.assign_points_to_user(
            gameId=game_id,
            externalTaskId="task-2",
            schema=schema,
            request=self._request(),
            service=service,
            abuse_prevention_service=self._abuse_service(),
            audit=self._audit(api_key="api-key-1", oauth_user_id=None),
        )

        self.assertEqual(result, {"points": 2})
        service.assign_points_to_user.assert_awaited_once_with(
            game_id,
            "task-2",
            schema,
            False,
            "api-key-1",
            oauth_user_id=None,
            is_admin=False,
            enforce_scope=True,
        )

    async def test_user_action_in_task_calls_abuse_prevention_service(self):
        game_id = uuid4()
        request = self._request(host="203.0.113.10")
        abuse_service = self._abuse_service(ip="203.0.113.10")
        schema = AddActionDidByUserInTask(
            typeAction="click",
            data={"x": 1},
            description="desc",
            externalUserId="u1",
        )
        service = AsyncMock()
        service.user_add_action_in_task = AsyncMock(return_value={"ok": True})

        await games.user_action_in_task(
            gameId=game_id,
            externalTaskId="task-1",
            schema=schema,
            request=request,
            service=service,
            abuse_prevention_service=abuse_service,
            audit=self._audit(api_key="api-key-abuse", oauth_user_id=None),
        )

        abuse_service.extract_client_ip.assert_called_once_with(request)
        abuse_service.enforce_task_mutation_limits.assert_called_once_with(
            api_key="api-key-abuse",
            client_ip="203.0.113.10",
            external_user_id="u1",
        )

    async def test_assign_points_to_user_raises_too_many_requests(self):
        game_id = uuid4()
        request = self._request(host="203.0.113.20")
        abuse_service = self._abuse_service(
            enforce_side_effect=TooManyRequestsError(detail="blocked")
        )
        schema = AsignPointsToExternalUserId(
            externalUserId="u1",
            data={"points": 1},
            isSimulated=False,
        )
        service = AsyncMock()
        service.assign_points_to_user = AsyncMock(return_value={"points": 99})

        with self.assertRaises(TooManyRequestsError):
            await games.assign_points_to_user(
                gameId=game_id,
                externalTaskId="task-1",
                schema=schema,
                request=request,
                service=service,
                abuse_prevention_service=abuse_service,
                audit=self._audit(api_key="api-key-abuse", oauth_user_id=None),
            )

        service.assign_points_to_user.assert_not_called()

    async def test_assign_points_to_user_maps_precondition_failed_to_422(self):
        game_id = uuid4()
        schema = AsignPointsToExternalUserId(
            externalUserId="u1",
            data={"points": 1},
            isSimulated=False,
        )
        service = AsyncMock()
        service.assign_points_to_user = AsyncMock(
            side_effect=PreconditionFailedError(detail="invalid scoring payload")
        )

        with self.assertRaises(HTTPException) as exc_info:
            await games.assign_points_to_user(
                gameId=game_id,
                externalTaskId="task-1",
                schema=schema,
                request=self._request(),
                service=service,
                abuse_prevention_service=self._abuse_service(),
                audit=self._audit(api_key="api-key-1", oauth_user_id=None),
            )

        self.assertEqual(exc_info.exception.status_code, 422)

    async def test_assign_points_to_user_maps_duplicated_error_to_409(self):
        game_id = uuid4()
        schema = AsignPointsToExternalUserId(
            externalUserId="u1",
            data={"points": 1},
            isSimulated=False,
        )
        service = AsyncMock()
        service.assign_points_to_user = AsyncMock(
            side_effect=DuplicatedError(detail="duplicate key")
        )

        with self.assertRaises(HTTPException) as exc_info:
            await games.assign_points_to_user(
                gameId=game_id,
                externalTaskId="task-1",
                schema=schema,
                request=self._request(),
                service=service,
                abuse_prevention_service=self._abuse_service(),
                audit=self._audit(api_key="api-key-1", oauth_user_id=None),
            )

        self.assertEqual(exc_info.exception.status_code, 409)

    async def test_get_points_by_task_id(self):
        service = AsyncMock()
        service.get_points_by_task_id.return_value = [{"externalUserId": "u1"}]
        game_id = uuid4()

        result = await games.get_points_by_task_id(
            gameId=game_id,
            externalTaskId="task-1",
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, [{"externalUserId": "u1"}])

    async def test_get_points_of_user_by_task_id(self):
        service = AsyncMock()
        service.get_points_of_user_by_task_id.return_value = {"externalUserId": "u1"}
        game_id = uuid4()

        result = await games.get_points_of_user_by_task_id(
            gameId=game_id,
            externalTaskId="task-1",
            externalUserId="u1",
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, {"externalUserId": "u1"})

    async def test_get_points_by_task_id_with_details(self):
        service = AsyncMock()
        service.get_points_by_task_id_with_details.return_value = [{"details": True}]
        game_id = uuid4()

        result = await games.get_points_by_task_id_with_details(
            gameId=game_id,
            externalTaskId="task-1",
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertEqual(result, [{"details": True}])

    async def test_get_users_by_game_id(self):
        service = AsyncMock()
        service.get_users_by_gameId.return_value = {
            "gameId": str(uuid4()),
            "tasks": [],
        }
        game_id = uuid4()

        result = await games.get_users_by_gameId(
            gameId=game_id,
            service=service,
            audit=self._audit(api_key="api-key-1", oauth_user_id="oauth-user-1"),
        )

        self.assertIn("tasks", result)

    async def test_token_absent_paths_cover_non_oauth_branches(self):
        game_id = uuid4()
        api_key_header = self._api_key_header("k-no-token")
        oauth_service = self._oauth_service(user_exists=True, async_add=True)

        get_by_id_service = AsyncMock()
        get_by_id_service.get_by_gameId.return_value = {"id": str(game_id)}
        result = await games.get_game_by_id(
            gameId=game_id,
            service=get_by_id_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result["id"], str(game_id))

        strategy_service = AsyncMock()
        strategy_service.get_strategy_by_gameId.return_value = {"id": "default"}
        result = await games.get_strategy_by_gameId(
            gameId=game_id,
            service=strategy_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result, {"id": "default"})

        bulk_service = AsyncMock()
        bulk_service.create_task_by_game_id = AsyncMock(
            side_effect=[{"task": "a"}, {"task": "b"}]
        )
        bulk_query = CreateTasksPost(
            tasks=[
                CreateTaskPost(
                    externalTaskId="task-a", strategyId="default", params=None
                ),
                CreateTaskPost(
                    externalTaskId="task-b", strategyId="default", params=None
                ),
            ]
        )
        result = await games.create_tasks_bulk(
            gameId=game_id,
            create_query=bulk_query,
            service=bulk_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result["failed_to_create"], [])
        self.assertEqual(len(result["succesfully_created"]), 2)

        list_service = AsyncMock()
        list_service.get_tasks_list_by_gameId.return_value = {"items": []}
        result = await games.get_task_list(
            gameId=game_id,
            find_query=PostFindTask(ordering="-created_at", page=1, page_size=10),
            service=list_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result, {"items": []})

        task_service = AsyncMock()
        task_service.get_task_by_externalGameId_externalTaskId.return_value = {
            "task": "one"
        }
        result = await games.get_task_by_gameId_taskId(
            gameId=game_id,
            externalTaskId="task-1",
            service=task_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result, {"task": "one"})

        points_service = AsyncMock()
        points_service.get_points_by_gameId.return_value = {"game": "points"}
        result = await games.get_points_by_gameId(
            gameId=game_id,
            service=points_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result, {"game": "points"})

        points_details_service = AsyncMock()
        points_details_service.get_points_by_gameId_with_details.return_value = {
            "game": "details"
        }
        result = await games.get_points_by_gameId_with_details(
            gameId=game_id,
            service=points_details_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result, {"game": "details"})

        user_points_service = AsyncMock()
        user_points_service.get_points_of_user_in_game.return_value = [
            {"externalUserId": "u1"}
        ]
        result = await games.get_points_of_user_in_game(
            gameId=game_id,
            externalUserId="u1",
            service=user_points_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result, [{"externalUserId": "u1"}])

        user_action_service = AsyncMock()
        user_action_service.user_add_action_in_task = AsyncMock(
            return_value={"ok": True}
        )
        action_schema = AddActionDidByUserInTask(
            typeAction="click",
            data={"x": 1},
            description="desc",
            externalUserId="u1",
        )
        result = await games.user_action_in_task(
            gameId=game_id,
            externalTaskId="task-1",
            schema=action_schema,
            request=self._request(),
            service=user_action_service,
            abuse_prevention_service=self._abuse_service(),
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result, {"ok": True})

        points_by_task_service = AsyncMock()
        points_by_task_service.get_points_by_task_id.return_value = [
            {"externalUserId": "u1"}
        ]
        result = await games.get_points_by_task_id(
            gameId=game_id,
            externalTaskId="task-1",
            service=points_by_task_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result, [{"externalUserId": "u1"}])

        user_points_by_task_service = AsyncMock()
        user_points_by_task_service.get_points_of_user_by_task_id.return_value = {
            "externalUserId": "u1"
        }
        result = await games.get_points_of_user_by_task_id(
            gameId=game_id,
            externalTaskId="task-1",
            externalUserId="u1",
            service=user_points_by_task_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result, {"externalUserId": "u1"})

        points_task_details_service = AsyncMock()
        points_task_details_service.get_points_by_task_id_with_details.return_value = [
            {"details": True}
        ]
        result = await games.get_points_by_task_id_with_details(
            gameId=game_id,
            externalTaskId="task-1",
            service=points_task_details_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result, [{"details": True}])

        users_by_game_service = AsyncMock()
        users_by_game_service.get_users_by_gameId.return_value = {
            "gameId": str(game_id),
            "tasks": [],
        }
        result = await games.get_users_by_gameId(
            gameId=game_id,
            service=users_by_game_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id=None),
        )
        self.assertEqual(result["gameId"], str(game_id))

    async def test_existing_oauth_user_paths_skip_creation_and_cover_non_happy_branches(
        self,
    ):
        game_id = uuid4()
        api_key_header = self._api_key_header("k-existing")
        token = "Bearer existing-user"
        oauth_service = self._oauth_service(user_exists=True, async_add=True)

        schema = PostFindGame(ordering="-created_at", page=1, page_size=10)
        games_list_service = AsyncMock()
        games_list_service.get_all_games.return_value = {"items": ["filtered"]}
        result = await games.get_games_list(
            schema=schema,
            service=games_list_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )
        self.assertEqual(result, {"items": ["filtered"]})
        games_list_service.get_all_games.assert_called_once_with(
            schema,
            api_key="k-existing",
            oauth_user_id="oauth-user-1",
            is_admin=False,
        )

        get_by_id_service = AsyncMock()
        get_by_id_service.get_by_gameId.return_value = {"id": str(game_id)}
        await games.get_game_by_id(
            gameId=game_id,
            service=get_by_id_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        delete_service = AsyncMock()
        delete_service.delete_game_by_id.return_value = {"gameId": str(game_id)}
        await games.delete_game_by_id(
            gameId=game_id,
            service=delete_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        create_service = AsyncMock()
        create_service.create = AsyncMock(return_value=SimpleNamespace(gameId=uuid4()))
        await games.create_game(
            schema=PostCreateGame(
                externalGameId="game_existing_user",
                platform="web",
                strategyId="default",
                params=[],
                apiKey_used=None,
                oauth_user_id=None,
            ),
            service=create_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        patch_service = AsyncMock()
        patch_service.patch_game_by_id = AsyncMock(return_value={"ok": True})
        await games.patch_game(
            gameId=game_id,
            schema=PatchGame(
                externalGameId="slug", strategyId="default", platform="web"
            ),
            service=patch_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        strategy_service = AsyncMock()
        strategy_service.get_strategy_by_gameId.return_value = {"id": "default"}
        await games.get_strategy_by_gameId(
            gameId=game_id,
            service=strategy_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        create_task_service = AsyncMock()
        create_task_service.create_task_by_game_id = AsyncMock(
            return_value={"task": "created"}
        )
        await games.create_task(
            gameId=game_id,
            create_query=CreateTaskPost(
                externalTaskId="task-existing-user",
                strategyId="default",
                params=[CreateTaskParams(key="k", value=1)],
            ),
            service=create_task_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        bulk_fail_service = AsyncMock()
        bulk_fail_service.create_task_by_game_id = AsyncMock(
            side_effect=[RuntimeError("fail-1"), RuntimeError("fail-2")]
        )
        bulk_result = await games.create_tasks_bulk(
            gameId=game_id,
            create_query=CreateTasksPost(
                tasks=[
                    CreateTaskPost(
                        externalTaskId="task-fail-1", strategyId="default", params=None
                    ),
                    CreateTaskPost(
                        externalTaskId="task-fail-2", strategyId="default", params=None
                    ),
                ]
            ),
            service=bulk_fail_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )
        self.assertEqual(len(bulk_result["succesfully_created"]), 0)
        self.assertEqual(len(bulk_result["failed_to_create"]), 2)

        list_service = AsyncMock()
        list_service.get_tasks_list_by_gameId.return_value = {"items": []}
        await games.get_task_list(
            gameId=game_id,
            find_query=PostFindTask(ordering="-created_at", page=1, page_size=10),
            service=list_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        task_service = AsyncMock()
        task_service.get_task_by_externalGameId_externalTaskId.return_value = {
            "task": "one"
        }
        await games.get_task_by_gameId_taskId(
            gameId=game_id,
            externalTaskId="task-1",
            service=task_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        points_service = AsyncMock()
        points_service.get_points_by_gameId.return_value = {"game": "points"}
        await games.get_points_by_gameId(
            gameId=game_id,
            service=points_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        points_details_service = AsyncMock()
        points_details_service.get_points_by_gameId_with_details.return_value = {
            "game": "details"
        }
        await games.get_points_by_gameId_with_details(
            gameId=game_id,
            service=points_details_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        user_points_service = AsyncMock()
        user_points_service.get_points_of_user_in_game.return_value = [
            {"externalUserId": "u1"}
        ]
        await games.get_points_of_user_in_game(
            gameId=game_id,
            externalUserId="u1",
            service=user_points_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

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
        simulated_service = AsyncMock()
        simulated_service.get_points_simulated_of_user_in_game = AsyncMock(
            return_value=(simulated_tasks, "external-game-1")
        )
        result = await games.get_points_simulated_of_user_in_game(
            gameId=game_id,
            externalUserId="oauth-user-1",
            service=simulated_service,
            audit=self._audit(api_key=None, oauth_user_id="oauth-user-1"),
            service_user=MagicMock(),
        )
        self.assertEqual(result.simulationHash, "sim-hash-1")

        user_action_service = AsyncMock()
        user_action_service.user_add_action_in_task = AsyncMock(
            return_value={"ok": True}
        )
        await games.user_action_in_task(
            gameId=game_id,
            externalTaskId="task-1",
            schema=AddActionDidByUserInTask(
                typeAction="click",
                data={"x": 1},
                description="desc",
                externalUserId="u1",
            ),
            request=self._request(),
            service=user_action_service,
            abuse_prevention_service=self._abuse_service(),
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        assign_points_service = AsyncMock()
        assign_points_service.assign_points_to_user = AsyncMock(
            return_value={"points": 1}
        )
        await games.assign_points_to_user(
            gameId=game_id,
            externalTaskId="task-1",
            schema=AsignPointsToExternalUserId(
                externalUserId="u1",
                data={"points": 1},
                isSimulated=False,
            ),
            request=self._request(),
            service=assign_points_service,
            abuse_prevention_service=self._abuse_service(),
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        points_by_task_service = AsyncMock()
        points_by_task_service.get_points_by_task_id.return_value = [
            {"externalUserId": "u1"}
        ]
        await games.get_points_by_task_id(
            gameId=game_id,
            externalTaskId="task-1",
            service=points_by_task_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        user_points_by_task_service = AsyncMock()
        user_points_by_task_service.get_points_of_user_by_task_id.return_value = {
            "externalUserId": "u1"
        }
        await games.get_points_of_user_by_task_id(
            gameId=game_id,
            externalTaskId="task-1",
            externalUserId="u1",
            service=user_points_by_task_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        points_task_details_service = AsyncMock()
        points_task_details_service.get_points_by_task_id_with_details.return_value = [
            {"details": True}
        ]
        await games.get_points_by_task_id_with_details(
            gameId=game_id,
            externalTaskId="task-1",
            service=points_task_details_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )

        users_by_game_service = AsyncMock()
        users_by_game_service.get_users_by_gameId.return_value = {
            "gameId": str(game_id),
            "tasks": [],
        }
        await games.get_users_by_gameId(
            gameId=game_id,
            service=users_by_game_service,
            audit=self._audit_from_header(api_key_header, oauth_user_id="oauth-user-1"),
        )


if __name__ == "__main__":
    unittest.main()
