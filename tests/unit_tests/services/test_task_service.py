import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.core.exceptions import ConflictError, NotFoundError
from app.repository.game_params_repository import GameParamsRepository
from app.repository.game_repository import GameRepository
from app.repository.task_params_repository import TaskParamsRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.schema.games_params_schema import CreateGameParams
from app.schema.task_schema import CreateTaskPost, PostFindTask
from app.schema.tasks_params_schema import CreateTaskParams
from app.services.strategy_service import StrategyService
from app.services.task_service import TaskService


class TestTaskService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.strategy_service_instance = MagicMock(spec=StrategyService)
        self.task_repository = MagicMock(spec=TaskRepository)
        self.game_repository = MagicMock(spec=GameRepository)
        self.user_repository = MagicMock(spec=UserRepository)
        self.user_points_repository = MagicMock(spec=UserPointsRepository)
        self.game_params_repository = MagicMock(spec=GameParamsRepository)
        self.task_params_repository = MagicMock(spec=TaskParamsRepository)

        self.service = TaskService(
            strategy_service=lambda: self.strategy_service_instance,
            task_repository=self.task_repository,
            game_repository=self.game_repository,
            user_repository=self.user_repository,
            user_points_repository=self.user_points_repository,
            game_params_repository=self.game_params_repository,
            task_params_repository=self.task_params_repository,
        )

    @staticmethod
    def _strategy_payload(
        strategy_id="default",
        variables=None,
    ):
        return {
            "id": strategy_id,
            "name": "Strategy",
            "description": "desc",
            "version": "1.0.0",
            "variables": variables or {},
            "hash_version": "hash",
        }

    @staticmethod
    def _game(game_id, external_game_id="external-game-1", strategy_id="default"):
        return SimpleNamespace(
            id=game_id,
            externalGameId=external_game_id,
            strategyId=strategy_id,
        )

    @staticmethod
    def _task(task_id, external_task_id="task-1", strategy_id="default"):
        task = SimpleNamespace(
            id=task_id,
            externalTaskId=external_task_id,
            strategyId=strategy_id,
        )
        task.dict = lambda: {
            "id": task_id,
            "externalTaskId": external_task_id,
            "strategyId": strategy_id,
        }
        return task

    def test_init_sets_dependencies(self):
        self.assertIs(self.service.task_repository, self.task_repository)
        self.assertIs(self.service.game_repository, self.game_repository)
        self.assertIs(self.service.user_repository, self.user_repository)
        self.assertIs(self.service.user_points_repository, self.user_points_repository)
        self.assertIs(self.service.game_params_repository, self.game_params_repository)
        self.assertIs(self.service.task_params_repository, self.task_params_repository)
        self.assertIs(self.service.strategy_service, self.strategy_service_instance)
        self.assertIs(self.service._repository, self.task_repository)

    def test_get_tasks_list_by_external_game_id_raises_when_game_missing(self):
        self.game_repository.read_by_column.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_tasks_list_by_externalGameId(
                "missing-game",
                PostFindTask(ordering="-created_at", page=1, page_size=10),
            )

    def test_get_tasks_list_by_external_game_id_delegates_to_game_id_method(self):
        game_id = uuid4()
        self.game_repository.read_by_column.return_value = self._game(game_id)
        self.service.get_tasks_list_by_gameId = MagicMock(return_value={"items": []})
        find_query = PostFindTask(ordering="-created_at", page=1, page_size=10)

        result = self.service.get_tasks_list_by_externalGameId("external-game-1", find_query)

        self.assertEqual(result, {"items": []})
        self.service.get_tasks_list_by_gameId.assert_called_once_with(game_id, find_query)

    def test_get_tasks_list_by_game_id_raises_when_game_missing(self):
        self.game_repository.read_by_id.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_tasks_list_by_gameId(
                uuid4(),
                PostFindTask(ordering="-created_at", page=1, page_size=10),
            )

    def test_get_tasks_list_by_game_id_returns_enriched_tasks(self):
        game_id = uuid4()
        task_id_1 = uuid4()
        task_id_2 = uuid4()
        game = self._game(game_id, strategy_id="strategy-A")
        self.game_repository.read_by_id.return_value = game
        find_query = PostFindTask(ordering="-created_at", page=1, page_size=10)
        task_1 = self._task(task_id_1, external_task_id="task-1", strategy_id="strategy-A")
        task_2 = self._task(task_id_2, external_task_id="task-2", strategy_id="strategy-B")
        all_tasks = {"items": [task_1, task_2], "search_options": {"total_count": 2}}
        self.task_repository.read_by_gameId.return_value = all_tasks

        def strategy_factory(strategy_id):
            return self._strategy_payload(
                strategy_id=strategy_id,
                variables={
                    "g_int": 0,
                    "g_float": 0.0,
                    "g_str": "",
                    "t_int": 0,
                    "t_float": 0.0,
                    "t_str": "",
                },
            )

        self.strategy_service_instance.get_strategy_by_id.side_effect = strategy_factory
        game_params = [
            CreateGameParams(key="g_int", value="7"),
            CreateGameParams(key="g_float", value="2.5"),
            CreateGameParams(key="g_str", value="text-value"),
        ]
        self.game_params_repository.read_by_column.return_value = game_params
        task_params_for_task_1 = [
            CreateTaskParams(key="t_int", value="9"),
            CreateTaskParams(key="t_float", value="6.5"),
            CreateTaskParams(key="t_str", value="alpha"),
        ]
        self.task_params_repository.read_by_column.side_effect = [
            task_params_for_task_1,
            None,
        ]

        result = self.service.get_tasks_list_by_gameId(game_id, find_query)

        self.assertEqual(len(result["items"]), 2)
        first_task = result["items"][0]
        second_task = result["items"][1]
        self.assertEqual(first_task["externalTaskId"], "task-1")
        self.assertEqual(first_task["strategy"]["variables"]["g_int"], 7)
        self.assertEqual(first_task["strategy"]["variables"]["g_float"], 0.0)
        self.assertEqual(first_task["strategy"]["variables"]["g_str"], "text-value")
        self.assertEqual(first_task["strategy"]["variables"]["t_int"], 9)
        self.assertEqual(first_task["strategy"]["variables"]["t_float"], 6.5)
        self.assertEqual(first_task["strategy"]["variables"]["t_str"], "alpha")
        self.assertEqual(first_task["gameParams"], game_params)
        self.assertEqual(first_task["taskParams"], task_params_for_task_1)
        self.assertEqual(second_task["taskParams"], [])

    def test_get_task_by_game_id_external_task_id_raises_when_game_missing(self):
        self.game_repository.read_by_id.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_task_by_gameId_externalTaskId(uuid4(), "task-x")

    def test_get_task_by_game_id_external_task_id_raises_when_task_missing(self):
        game_id = uuid4()
        game = self._game(game_id)
        self.game_repository.read_by_id.return_value = game
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_task_by_gameId_externalTaskId(game_id, "missing-task")

    def test_get_task_by_game_id_external_task_id_returns_task_details(self):
        game_id = uuid4()
        task_id = uuid4()
        game = self._game(game_id, external_game_id="external-game-1")
        task = self._task(task_id, external_task_id="task-1", strategy_id="strategy-A")
        self.game_repository.read_by_id.return_value = game
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = task
        self.strategy_service_instance.get_strategy_by_id.return_value = self._strategy_payload(
            strategy_id="strategy-A",
            variables={
                "g_int": 0,
                "g_float": 0.0,
                "g_str": "",
                "t_int": 0,
                "t_str": "",
            },
        )
        game_params = [
            CreateGameParams(key="g_int", value="5"),
            CreateGameParams(key="g_float", value="1.5"),
            CreateGameParams(key="g_str", value="game-text"),
        ]
        task_params = [
            CreateTaskParams(key="t_int", value="4"),
            CreateTaskParams(key="t_str", value="task-text"),
        ]
        self.game_params_repository.read_by_column.return_value = game_params
        self.task_params_repository.read_by_column.return_value = task_params

        result = self.service.get_task_by_gameId_externalTaskId(game_id, "task-1")

        self.assertEqual(result.externalTaskId, "task-1")
        self.assertEqual(result.externalGameId, "external-game-1")
        self.assertEqual(result.strategy.variables["g_int"], 5)
        self.assertEqual(result.strategy.variables["g_float"], 1.5)
        self.assertEqual(result.strategy.variables["g_str"], "game-text")
        self.assertEqual(result.strategy.variables["t_int"], 4)
        self.assertEqual(result.strategy.variables["t_str"], "task-text")
        self.assertEqual(result.gameParams, game_params)
        self.assertEqual(result.taskParams, task_params)

    def test_get_task_by_external_game_id_external_task_id_delegates(self):
        game_id = uuid4()
        self.game_repository.read_by_column.return_value = self._game(game_id)
        self.service.get_task_by_gameId_externalTaskId = MagicMock(return_value="task-data")

        result = self.service.get_task_by_externalGameId_externalTaskId(game_id, "task-1")

        self.assertEqual(result, "task-data")
        self.service.get_task_by_gameId_externalTaskId.assert_called_once_with(
            game_id, "task-1"
        )

    async def test_create_task_by_external_game_id_delegates_to_game_id_method(self):
        game_id = uuid4()
        self.game_repository.read_by_column.return_value = self._game(game_id)
        self.service.create_task_by_game_id = AsyncMock(return_value="created")
        create_query = CreateTaskPost(externalTaskId="task-1", strategyId=None, params=None)

        result = await self.service.create_task_by_externalGameId(
            "external-game-1", create_query
        )

        self.assertEqual(result, "created")
        self.service.create_task_by_game_id.assert_awaited_once_with(
            game_id,
            "external-game-1",
            create_query,
        )

    async def test_create_task_by_game_id_raises_when_game_missing(self):
        self.game_repository.read_by_id.return_value = None
        create_query = CreateTaskPost(externalTaskId="task-1", strategyId=None, params=None)

        with self.assertRaises(NotFoundError):
            await self.service.create_task_by_game_id(uuid4(), create_query)

    async def test_create_task_by_game_id_raises_when_task_already_exists(self):
        game_id = uuid4()
        self.game_repository.read_by_id.return_value = self._game(game_id)
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = self._task(
            uuid4()
        )
        create_query = CreateTaskPost(
            externalTaskId="task-duplicated", strategyId="default", params=None
        )

        with self.assertRaises(ConflictError):
            await self.service.create_task_by_game_id(game_id, create_query)

    async def test_create_task_by_game_id_raises_when_strategy_missing(self):
        game_id = uuid4()
        self.game_repository.read_by_id.return_value = self._game(game_id)
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = None
        self.strategy_service_instance.get_strategy_by_id.return_value = None
        create_query = CreateTaskPost(
            externalTaskId="task-1", strategyId="missing-strategy", params=None
        )

        with self.assertRaises(NotFoundError):
            await self.service.create_task_by_game_id(game_id, create_query)

    async def test_create_task_by_game_id_defaults_strategy_when_none(self):
        game_id = uuid4()
        created_task_id = uuid4()
        game_data = self._game(game_id, external_game_id="external-game-2")
        self.game_repository.read_by_id.return_value = game_data
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = None
        self.strategy_service_instance.get_strategy_by_id.return_value = self._strategy_payload(
            strategy_id="default",
            variables={"k": 1},
        )
        created_task = self._task(created_task_id, external_task_id="task-1")
        self.task_repository.create = AsyncMock(return_value=created_task)
        self.game_params_repository.read_by_column.return_value = None
        create_query = CreateTaskPost(externalTaskId="task-1", strategyId=None, params=None)

        result = await self.service.create_task_by_game_id(game_id, create_query)

        self.assertEqual(result.externalTaskId, "task-1")
        self.assertEqual(result.externalGameId, "external-game-2")
        self.assertEqual(result.taskParams, [])
        created_payload = self.task_repository.create.await_args.args[0]
        self.assertEqual(created_payload.strategyId, "default")

    async def test_create_task_by_game_id_creates_params_and_applies_variables(self):
        game_id = uuid4()
        created_task_id = uuid4()
        game_data = self._game(game_id, external_game_id="external-game-3")
        self.game_repository.read_by_id.return_value = game_data
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = None

        def strategy_factory(_strategy_id):
            return self._strategy_payload(
                strategy_id="strategy-A",
                variables={
                    "g_int": 0,
                    "g_float": 0.0,
                    "g_str": "",
                    "t_int": 0,
                    "t_float": 0.0,
                    "t_str": "",
                },
            )

        self.strategy_service_instance.get_strategy_by_id.side_effect = strategy_factory
        created_task = self._task(
            created_task_id, external_task_id="task-rich", strategy_id="strategy-A"
        )
        self.task_repository.create = AsyncMock(return_value=created_task)
        created_param_1 = CreateTaskParams(key="t_int", value="11")
        created_param_2 = CreateTaskParams(key="t_float", value="6.75")
        created_param_3 = CreateTaskParams(key="t_str", value="task-level-text")
        self.task_params_repository.create = AsyncMock(
            side_effect=[created_param_1, created_param_2, created_param_3]
        )
        game_params = [
            CreateGameParams(key="g_int", value="7"),
            CreateGameParams(key="g_float", value="2.5"),
            CreateGameParams(key="g_str", value="game-level-text"),
        ]
        self.game_params_repository.read_by_column.return_value = game_params
        create_query = CreateTaskPost(
            externalTaskId="task-rich",
            strategyId="strategy-A",
            params=[
                CreateTaskParams(key="t_int", value=9),
                CreateTaskParams(key="t_float", value=3.5),
                CreateTaskParams(key="t_str", value="raw-text"),
            ],
        )

        result = await self.service.create_task_by_game_id(
            game_id, create_query, api_key="api-key"
        )

        self.assertEqual(result.externalTaskId, "task-rich")
        self.assertEqual(result.externalGameId, "external-game-3")
        self.assertEqual(result.strategy.variables["g_int"], 7)
        self.assertEqual(result.strategy.variables["g_float"], 2.5)
        self.assertEqual(result.strategy.variables["g_str"], "game-level-text")
        self.assertEqual(result.strategy.variables["t_int"], 11)
        self.assertEqual(result.strategy.variables["t_float"], 6.75)
        self.assertEqual(result.strategy.variables["t_str"], "task-level-text")
        self.assertEqual(len(result.taskParams), 3)
        created_payload = self.task_repository.create.await_args.args[0]
        self.assertEqual(created_payload.apiKey_used, "api-key")
        first_insert_payload = self.task_params_repository.create.await_args_list[0].args[0]
        self.assertEqual(first_insert_payload.value, "9")
        self.assertEqual(first_insert_payload.apiKey_used, "api-key")

    def test_get_task_detail_by_id_returns_task_and_strategy(self):
        task_id = uuid4()
        task = SimpleNamespace(id=task_id, strategyId="strategy-A")
        self.task_repository.read_by_id.return_value = task
        self.service.strategy_repository = MagicMock()
        expected_strategy = {"id": "strategy-A"}
        self.service.strategy_repository.read_by_id.return_value = expected_strategy
        schema = SimpleNamespace(taskId=task_id)

        result = self.service.get_task_detail_by_id(schema)

        self.assertEqual(result, {"task": task, "strategy": expected_strategy})

    def test_get_task_detail_by_id_returns_task_with_none_strategy(self):
        task_id = uuid4()
        task = SimpleNamespace(id=task_id, strategyId=None)
        self.task_repository.read_by_id.return_value = task
        schema = SimpleNamespace(taskId=task_id)

        result = self.service.get_task_detail_by_id(schema)

        self.assertEqual(result, {"task": task, "strategy": None})

    def test_get_points_by_task_id_raises_when_task_missing(self):
        game_id = uuid4()
        self.game_repository.read_by_column.return_value = self._game(game_id)
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_points_by_task_id(game_id, "missing-task")

    def test_get_points_by_task_id_returns_user_points(self):
        game_id = uuid4()
        task_id = uuid4()
        self.game_repository.read_by_column.return_value = self._game(game_id)
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = self._task(
            task_id
        )
        self.user_points_repository.get_all_UserPoints_by_taskId.return_value = [
            {"points": 3}
        ]

        result = self.service.get_points_by_task_id(game_id, "task-1")

        self.assertEqual(result, [{"points": 3}])

    def test_get_points_of_user_by_task_id_raises_when_user_points_missing(self):
        self.service.get_points_by_task_id_with_details = MagicMock(return_value=[])

        with self.assertRaises(NotFoundError):
            self.service.get_points_of_user_by_task_id(uuid4(), "task-1", "user-x")

    def test_get_points_of_user_by_task_id_returns_first_matching_user(self):
        matching = SimpleNamespace(externalUserId="user-1", points=8)
        self.service.get_points_by_task_id_with_details = MagicMock(
            return_value=[SimpleNamespace(externalUserId="user-2"), matching]
        )

        result = self.service.get_points_of_user_by_task_id(uuid4(), "task-1", "user-1")

        self.assertEqual(result, matching)

    def test_get_points_by_task_id_with_details_raises_when_task_missing(self):
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_points_by_task_id_with_details(uuid4(), "missing-task")

    def test_get_points_by_task_id_with_details_returns_points(self):
        task_id = uuid4()
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = self._task(
            task_id
        )
        self.user_points_repository.get_all_UserPoints_by_taskId_with_details.return_value = [
            {"externalUserId": "user-1", "pointsData": []}
        ]

        result = self.service.get_points_by_task_id_with_details(uuid4(), "task-1")

        self.assertEqual(result, [{"externalUserId": "user-1", "pointsData": []}])

    def test_get_task_params_by_external_task_id_returns_params(self):
        task_id = uuid4()
        task = self._task(task_id, external_task_id="task-1")
        self.task_repository.read_by_column.return_value = task
        expected_params = [CreateTaskParams(key="k", value="v")]
        self.task_params_repository.read_by_column.return_value = expected_params

        result = self.service.get_task_params_by_externalTaskId("task-1")

        self.assertEqual(result, expected_params)
        self.task_params_repository.read_by_column.assert_called_once_with(
            "taskId",
            task_id,
            not_found_raise_exception=False,
            only_one=False,
        )


if __name__ == "__main__":
    unittest.main()
