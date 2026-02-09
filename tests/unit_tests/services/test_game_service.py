import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.core.exceptions import ConflictError, NotFoundError
from app.repository.game_params_repository import GameParamsRepository
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.schema.games_params_schema import CreateGameParams, UpdateGameParams
from app.schema.games_schema import PatchGame, PostCreateGame
from app.services.game_service import GameService
from app.services.strategy_service import StrategyService


class TestGameService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.game_repository = MagicMock(spec=GameRepository)
        self.game_params_repository = MagicMock(spec=GameParamsRepository)
        self.task_repository = MagicMock(spec=TaskRepository)
        self.user_points_repository = MagicMock(spec=UserPointsRepository)
        self.strategy_service = MagicMock(spec=StrategyService)

        self.service = GameService(
            game_repository=self.game_repository,
            game_params_repository=self.game_params_repository,
            task_repository=self.task_repository,
            user_points_repository=self.user_points_repository,
            strategy_service=self.strategy_service,
        )

    @staticmethod
    def _build_game(
        game_id,
        external_game_id="external-game-1",
        strategy_id="default",
        platform="web",
        created_at=datetime(2026, 1, 1, 0, 0, 0),
        updated_at=datetime(2026, 1, 2, 0, 0, 0),
        include_params=False,
    ):
        game = SimpleNamespace(
            id=game_id,
            externalGameId=external_game_id,
            strategyId=strategy_id,
            platform=platform,
            created_at=created_at,
            updated_at=updated_at,
        )
        payload = {
            "id": game_id,
            "externalGameId": external_game_id,
            "strategyId": strategy_id,
            "platform": platform,
            "created_at": created_at,
            "updated_at": updated_at,
        }
        if include_params:
            payload["params"] = []
        game.dict = lambda: payload
        return game

    def test_init_sets_dependencies(self):
        self.assertIs(self.service.game_repository, self.game_repository)
        self.assertIs(self.service.game_params_repository, self.game_params_repository)
        self.assertIs(self.service.task_repository, self.task_repository)
        self.assertIs(self.service.strategy_service, self.strategy_service)
        self.assertIs(self.service._repository, self.game_repository)

    def test_get_by_game_id_returns_game_with_params(self):
        game_id = uuid4()
        game = self._build_game(game_id)
        params = [SimpleNamespace(id=uuid4(), key="multiplier", value="2")]
        self.game_repository.read_by_column.return_value = game
        self.game_params_repository.read_by_column.return_value = params

        result = self.service.get_by_gameId(game_id)

        self.assertEqual(result.gameId, game_id)
        self.assertEqual(result.externalGameId, "external-game-1")
        self.assertEqual(result.params[0].key, "multiplier")

    def test_delete_game_by_id_raises_when_game_not_found(self):
        game_id = uuid4()
        self.game_repository.read_by_id.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.delete_game_by_id(game_id)

    def test_delete_game_by_id_returns_deleted_message(self):
        game_id = uuid4()
        game = self._build_game(game_id, strategy_id="strategy-1")
        self.game_repository.read_by_id.return_value = game
        self.game_repository.delete_game_by_id.return_value = True

        result = self.service.delete_game_by_id(game_id)

        self.assertEqual(result.gameId, game_id)
        self.assertEqual(result.externalGameId, "external-game-1")
        self.assertEqual(result.strategyId, "strategy-1")
        self.assertEqual(result.params, [])

    def test_delete_game_by_id_returns_not_deleted_message(self):
        game_id = uuid4()
        self.game_repository.read_by_id.return_value = self._build_game(game_id)
        self.game_repository.delete_game_by_id.return_value = False

        result = self.service.delete_game_by_id(game_id)

        self.assertEqual(
            result, {"message": f"Game with gameId: {game_id} not deleted"}
        )

    def test_get_all_games_delegates_to_repository(self):
        schema = SimpleNamespace(ordering="-created_at")
        expected = {"items": []}
        self.game_repository.get_all_games.return_value = expected

        result = self.service.get_all_games(schema, api_key="api-key")

        self.assertEqual(result, expected)
        self.game_repository.get_all_games.assert_called_once_with(schema, "api-key")

    def test_get_by_external_id_delegates_to_repository(self):
        game = self._build_game(uuid4())
        self.game_repository.read_by_column.return_value = game

        result = self.service.get_by_externalId("external-game-1")

        self.assertEqual(result, game)
        self.game_repository.read_by_column.assert_called_once_with(
            "externalGameId", "external-game-1"
        )

    async def test_create_raises_conflict_when_slug_invalid(self):
        schema = PostCreateGame(
            externalGameId="invalid-slug!",
            platform="web",
            strategyId="default",
            params=[],
            apiKey_used=None,
            oauth_user_id=None,
        )
        self.game_repository.read_by_column.return_value = None

        with self.assertRaises(ConflictError):
            await self.service.create(schema)

    async def test_create_raises_conflict_when_external_game_id_exists(self):
        existing_game = SimpleNamespace(id=uuid4())
        self.game_repository.read_by_column.return_value = existing_game
        schema = PostCreateGame(
            externalGameId="existing_game",
            platform="web",
            strategyId="default",
            params=[],
            apiKey_used=None,
            oauth_user_id=None,
        )

        with self.assertRaises(ConflictError):
            await self.service.create(schema)

    @patch("app.services.game_service.all_engine_strategies", return_value=[])
    async def test_create_raises_not_found_when_strategy_does_not_exist(
        self, _mock_strategies
    ):
        self.game_repository.read_by_column.return_value = None
        schema = PostCreateGame(
            externalGameId="new_game",
            platform="web",
            strategyId="non-existing",
            params=[],
            apiKey_used=None,
            oauth_user_id=None,
        )

        with self.assertRaises(NotFoundError):
            await self.service.create(schema)

    @patch(
        "app.services.game_service.all_engine_strategies",
        return_value=[SimpleNamespace(id="default")],
    )
    async def test_create_sets_default_strategy_and_creates_game_without_params(
        self, _mock_strategies
    ):
        game_id = uuid4()
        created_game = self._build_game(game_id, external_game_id="new_game")
        self.game_repository.read_by_column.return_value = None
        self.game_repository.create = AsyncMock(return_value=created_game)
        schema = PostCreateGame(
            externalGameId="new_game",
            platform="web",
            strategyId=None,
            params=None,
            apiKey_used=None,
            oauth_user_id=None,
        )

        result = await self.service.create(
            schema, api_key="api-key", oauth_user_id="oauth-user-1"
        )

        self.assertEqual(result.gameId, game_id)
        self.assertEqual(result.externalGameId, "new_game")
        self.assertEqual(result.params, [])
        self.assertEqual(schema.apiKey_used, "api-key")
        self.assertEqual(schema.oauth_user_id, "oauth-user-1")
        self.game_repository.create.assert_awaited_once_with(schema)

    @patch(
        "app.services.game_service.all_engine_strategies",
        return_value=[SimpleNamespace(id="default")],
    )
    async def test_create_with_params_creates_game_params_with_context(
        self, _mock_strategies
    ):
        game_id = uuid4()
        created_game = self._build_game(
            game_id, external_game_id="new_game_with_params"
        )
        created_param = SimpleNamespace(id=uuid4(), key="weight", value=5)
        self.game_repository.read_by_column.return_value = None
        self.game_repository.create = AsyncMock(return_value=created_game)
        self.game_params_repository.create = AsyncMock(return_value=created_param)
        schema = PostCreateGame(
            externalGameId="new_game_with_params",
            platform="mobile",
            strategyId="default",
            params=[CreateGameParams(key="weight", value=5)],
            apiKey_used=None,
            oauth_user_id=None,
        )

        result = await self.service.create(
            schema, api_key="api-key", oauth_user_id="oauth-user-2"
        )

        self.assertEqual(result.gameId, game_id)
        self.assertEqual(len(result.params), 1)
        insert_payload = self.game_params_repository.create.await_args.args[0]
        self.assertEqual(insert_payload.gameId, str(game_id))
        self.assertEqual(insert_payload.apiKey_used, "api-key")
        self.assertEqual(insert_payload.oauth_user_id, "oauth-user-2")

    def test_patch_game_by_external_game_id_raises_when_not_found(self):
        self.game_repository.read_by_column.return_value = None
        schema = PatchGame(
            externalGameId=None,
            strategyId=None,
            platform="web",
            params=None,
        )

        with self.assertRaises(NotFoundError):
            self.service.patch_game_by_externalGameId("missing-external-id", schema)

    def test_patch_game_by_external_game_id_delegates_to_patch_by_id(self):
        game_id = uuid4()
        schema = PatchGame(
            externalGameId=None,
            strategyId=None,
            platform="web",
            params=None,
        )
        self.game_repository.read_by_column.return_value = SimpleNamespace(id=game_id)
        self.service.patch_game_by_id = MagicMock(return_value="patched-result")

        result = self.service.patch_game_by_externalGameId("external-id", schema)

        self.assertEqual(result, "patched-result")
        self.service.patch_game_by_id.assert_called_once_with(game_id, schema)

    def test_patch_game_by_id_raises_when_game_not_found(self):
        game_id = uuid4()
        schema = PatchGame(
            externalGameId="new_external",
            strategyId=None,
            platform="web",
            params=None,
        )
        self.game_repository.read_by_id.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.patch_game_by_id(game_id, schema)

    def test_patch_game_by_id_raises_when_external_game_id_is_duplicated(self):
        game_id = uuid4()
        game = self._build_game(
            game_id, external_game_id="old_external", include_params=True
        )
        schema = PatchGame(
            externalGameId="new_external",
            strategyId=None,
            platform="web",
            params=None,
        )
        self.game_repository.read_by_id.return_value = game
        self.game_repository.read_by_column.return_value = SimpleNamespace(id=uuid4())

        with self.assertRaises(ConflictError):
            self.service.patch_game_by_id(game_id, schema)

    @patch("app.services.game_service.are_variables_matching", side_effect=[True, True])
    def test_patch_game_by_id_raises_when_data_and_params_are_equal(self, _mock_match):
        game_id = uuid4()
        param_id = uuid4()
        existing_param = SimpleNamespace(id=param_id, key="k", value="v")
        game = self._build_game(game_id, include_params=True)
        game.dict = lambda: {
            "externalGameId": "game_slug_1",
            "strategyId": "default",
            "platform": "web",
            "params": [existing_param],
        }
        schema = PatchGame(
            externalGameId="game_slug_1",
            strategyId="default",
            platform="web",
            params=[UpdateGameParams(id=param_id, key="k", value="v")],
        )
        self.game_repository.read_by_id.return_value = game
        self.game_repository.read_by_column.return_value = None

        with self.assertRaises(ConflictError) as context:
            self.service.patch_game_by_id(game_id, schema)
        self.assertIn("same data", context.exception.detail)

    @patch("app.services.game_service.are_variables_matching", return_value=False)
    def test_patch_game_by_id_raises_when_schema_dict_equals_game_dict(
        self, _mock_match
    ):
        game_id = uuid4()
        param_id = uuid4()
        same_dict = {
            "externalGameId": "same_game",
            "strategyId": "default",
            "platform": "web",
            "params": [{"id": param_id, "key": "k", "value": "v"}],
        }
        game = self._build_game(
            game_id, external_game_id="same_game", include_params=True
        )
        game.dict = lambda: same_dict
        schema = PatchGame(
            externalGameId="same_game",
            strategyId="default",
            platform="web",
            params=[UpdateGameParams(id=param_id, key="k", value="v")],
        )
        self.game_repository.read_by_id.return_value = game

        with self.assertRaises(ConflictError):
            self.service.patch_game_by_id(game_id, schema)

    @patch("app.services.game_service.all_engine_strategies", return_value=[])
    def test_patch_game_by_id_raises_when_strategy_not_found(self, _mock_strategies):
        game_id = uuid4()
        game = self._build_game(game_id, include_params=True)
        schema = PatchGame(
            externalGameId="new_slug_game",
            strategyId="missing_strategy",
            platform="web",
            params=None,
        )
        self.game_repository.read_by_id.return_value = game
        self.game_repository.read_by_column.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.patch_game_by_id(game_id, schema)

    @patch(
        "app.services.game_service.all_engine_strategies",
        return_value=[SimpleNamespace(id="default")],
    )
    def test_patch_game_by_id_uses_default_when_strategy_missing_in_schema_and_game(
        self, _mock_strategies
    ):
        game_id = uuid4()
        game = self._build_game(game_id, strategy_id=None, include_params=True)
        schema = PatchGame(
            externalGameId="new_slug_game",
            strategyId=None,
            platform="mobile",
            params=None,
        )
        patched_game = self._build_game(
            game_id,
            external_game_id="new_slug_game",
            platform="mobile",
        )
        self.game_repository.read_by_id.return_value = game
        self.game_repository.read_by_column.return_value = None
        self.game_repository.patch_game_by_id.return_value = patched_game

        result = self.service.patch_game_by_id(game_id, schema)

        self.assertEqual(result.strategyId, "default")
        self.assertEqual(result.platform, "mobile")
        self.assertEqual(result.params, [])

    def test_patch_game_by_id_updates_params_and_uses_game_strategy(self):
        game_id = uuid4()
        param_id = uuid4()
        update_param = UpdateGameParams(id=param_id, key="threshold", value=3)
        game = self._build_game(
            game_id, strategy_id="strategy_from_game", include_params=True
        )
        schema = PatchGame(
            externalGameId="new_slug_game",
            strategyId=None,
            platform="web",
            params=[update_param],
        )
        patched_game = self._build_game(
            game_id,
            external_game_id="new_slug_game",
            strategy_id="strategy_from_game",
            platform="web",
        )
        self.game_repository.read_by_id.return_value = game
        self.game_repository.read_by_column.return_value = None
        self.game_repository.patch_game_by_id.return_value = patched_game

        result = self.service.patch_game_by_id(game_id, schema)

        self.assertEqual(result.strategyId, "strategy_from_game")
        self.assertEqual(result.params[0].id, param_id)
        self.game_params_repository.patch_game_params_by_id.assert_called_once_with(
            param_id, update_param
        )

    def test_get_strategy_by_external_game_id_raises_when_game_missing(self):
        self.game_repository.read_by_column.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_strategy_by_externalGameId("missing-ext")

    def test_get_strategy_by_external_game_id_delegates_to_game_id_method(self):
        game_id = uuid4()
        self.game_repository.read_by_column.return_value = SimpleNamespace(id=game_id)
        self.service.get_strategy_by_gameId = MagicMock(return_value={"id": "default"})

        result = self.service.get_strategy_by_externalGameId("ext-1")

        self.assertEqual(result, {"id": "default"})
        self.service.get_strategy_by_gameId.assert_called_once_with(game_id)

    def test_get_strategy_by_game_id_raises_when_game_not_found(self):
        self.game_repository.read_by_id.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_strategy_by_gameId(uuid4())

    def test_get_strategy_by_game_id_raises_when_strategy_id_missing(self):
        game = self._build_game(uuid4(), strategy_id=None)
        self.game_repository.read_by_id.return_value = game

        with self.assertRaises(ConflictError):
            self.service.get_strategy_by_gameId(uuid4())

    def test_get_strategy_by_game_id_applies_game_params_with_type_coercion(self):
        game_id = uuid4()
        game = self._build_game(game_id, strategy_id="default")
        self.game_repository.read_by_id.return_value = game
        strategy_payload = {
            "id": "default",
            "variables": {
                "int_var": 1,
                "float_var": 1.0,
                "str_var": "base",
                "keep_int": 7,
            },
        }
        self.strategy_service.get_strategy_by_id.return_value = strategy_payload
        game_params = [
            SimpleNamespace(key="int_var", value="10"),
            SimpleNamespace(key="float_var", value="3.5"),
            SimpleNamespace(key="str_var", value="abc"),
            SimpleNamespace(key="keep_int", value="2.5"),
            SimpleNamespace(key="unknown", value="11"),
        ]
        self.game_params_repository.read_by_column.return_value = game_params

        result = self.service.get_strategy_by_gameId(game_id)

        self.assertEqual(result["variables"]["int_var"], 10)
        self.assertEqual(result["variables"]["float_var"], 3.5)
        self.assertEqual(result["variables"]["str_var"], "abc")
        self.assertEqual(result["variables"]["keep_int"], 7)
        self.assertEqual(result["game_params"], game_params)

    def test_get_strategy_by_game_id_returns_strategy_when_no_game_params(self):
        game_id = uuid4()
        game = self._build_game(game_id, strategy_id="default")
        self.game_repository.read_by_id.return_value = game
        strategy_payload = {"id": "default", "variables": {"k": 1}}
        self.strategy_service.get_strategy_by_id.return_value = strategy_payload
        self.game_params_repository.read_by_column.return_value = []

        result = self.service.get_strategy_by_gameId(game_id)

        self.assertEqual(result["variables"]["k"], 1)
        self.assertEqual(result["game_params"], [])

    def test_get_tasks_by_game_id_raises_when_game_missing(self):
        self.game_repository.read_by_id.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_tasks_by_gameId(uuid4())

    def test_get_tasks_by_game_id_returns_game_with_tasks(self):
        game_id = uuid4()
        game = self._build_game(game_id)
        self.game_repository.read_by_id.return_value = game
        self.task_repository.read_by_column.return_value = [
            SimpleNamespace(
                dict=lambda: {"id": str(uuid4()), "externalTaskId": "task-1"}
            )
        ]

        result = self.service.get_tasks_by_gameId(game_id)

        self.assertEqual(result["externalGameId"], "external-game-1")
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0]["externalTaskId"], "task-1")

    def test_get_tasks_by_game_id_returns_empty_task_list(self):
        game_id = uuid4()
        game = self._build_game(game_id)
        self.game_repository.read_by_id.return_value = game
        self.task_repository.read_by_column.return_value = []

        result = self.service.get_tasks_by_gameId(game_id)

        self.assertEqual(result["tasks"], [])

    def test_get_game_by_external_id_raises_when_game_missing(self):
        self.game_repository.read_by_column.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_game_by_external_id("missing-ext")

    def test_get_game_by_external_id_sets_api_key_and_oauth_user_id(self):
        game = self._build_game(uuid4())
        self.game_repository.read_by_column.return_value = game

        result = self.service.get_game_by_external_id(
            "external-game-1", api_key="api-key", oauth_user_id="oauth-1"
        )

        self.assertEqual(result.apiKey_used, "api-key")
        self.assertEqual(result.oauth_user_id, "oauth-1")


if __name__ == "__main__":
    unittest.main()
