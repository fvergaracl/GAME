import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import (InternalServerError, NotFoundError,
                                 PreconditionFailedError)
from app.schema.user_points_schema import PointsByUserInTask
from app.services.user_points_service import UserPointsService


class TestUserPointsService(unittest.IsolatedAsyncioTestCase):
    GAME_UUID = "00000000-0000-0000-0000-000000000001"

    def setUp(self):
        self.user_points_repository = MagicMock()
        self.users_repository = MagicMock()
        self.users_game_config_repository = MagicMock()
        self.game_repository = MagicMock()
        self.task_repository = MagicMock()
        self.wallet_repository = MagicMock()
        self.wallet_transaction_repository = MagicMock()

        self.service = UserPointsService(
            user_points_repository=self.user_points_repository,
            users_repository=self.users_repository,
            users_game_config_repository=self.users_game_config_repository,
            game_repository=self.game_repository,
            task_repository=self.task_repository,
            wallet_repository=self.wallet_repository,
            wallet_transaction_repository=self.wallet_transaction_repository,
        )

    def _setup_default_game_task_for_assignment(self):
        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1", externalGameId="external-game-1"
        )
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = (
            SimpleNamespace(id="task-1", strategyId="strategy-1")
        )

    async def test_assign_points_to_user_directly_handles_positive_points(self):
        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1", externalGameId="external-game-1"
        )
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = (
            SimpleNamespace(id="task-1", strategyId="default")
        )
        self.service.strategy_service.get_Class_by_id = MagicMock(return_value=object())
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-1", externalUserId="user_1"
        )
        self.user_points_repository.create = AsyncMock(
            return_value=SimpleNamespace(created_at="2026-02-09T00:00:00")
        )
        wallet = SimpleNamespace(id="wallet-1", pointsBalance=10)
        self.wallet_repository.read_by_column.return_value = wallet
        self.wallet_repository.update = AsyncMock(return_value=wallet)
        self.wallet_transaction_repository.create = AsyncMock(
            return_value=SimpleNamespace(id="txn-1")
        )

        schema = SimpleNamespace(externalUserId="user_1", data={"points": 5})
        response = await self.service.assign_points_to_user_directly(
            self.GAME_UUID, "task-external-1", schema, "api-key"
        )

        self.assertEqual(response.points, 5)
        self.assertEqual(response.caseName, "External_points_assigned")
        self.wallet_repository.update.assert_awaited_once()
        self.wallet_transaction_repository.create.assert_awaited_once()

    async def test_assign_points_to_user_raises_internal_error_when_case_name_missing(
        self,
    ):
        class StrategyWithoutCaseName:
            async def calculate_points(
                self, externalGameId, externalTaskId, externalUserId, data
            ):  # noqa
                return (5, None, None)

        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1", externalGameId="external-game-1"
        )
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = (
            SimpleNamespace(id="task-1", strategyId="default")
        )
        self.service.strategy_service.get_strategy_by_id = MagicMock(
            return_value=object()
        )
        self.service.strategy_service.get_Class_by_id = MagicMock(
            return_value=StrategyWithoutCaseName()
        )
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-1", externalUserId="user_1"
        )

        schema = SimpleNamespace(externalUserId="user_1", data={})
        with self.assertRaises(InternalServerError):
            await self.service.assign_points_to_user(
                self.GAME_UUID, "task-external-1", schema, False, "api-key"
            )

    def test_get_users_points_by_external_game_id_uses_task_identifier(self):
        self.game_repository.read_by_column.return_value = SimpleNamespace(id="game-1")
        self.task_repository.read_by_column.return_value = [
            SimpleNamespace(id="task-id-1", externalTaskId="task-external-1"),
            SimpleNamespace(id="task-id-2", externalTaskId="task-external-2"),
        ]
        self.user_points_repository.get_points_and_users_by_taskId.side_effect = [
            [SimpleNamespace(externalUserId="user_1", points=10)],
            [SimpleNamespace(externalUserId="user_2", points=20)],
        ]

        result = self.service.get_users_points_by_externalGameId("external-game-1")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].externalTaskId, "task-external-1")
        self.assertEqual(result[1].externalTaskId, "task-external-2")

    def test_get_all_points_by_external_user_id_aggregates_all_games(self):
        self.users_repository.read_by_column.return_value = SimpleNamespace(id="user-1")
        self.user_points_repository.get_task_by_externalUserId.return_value = [
            SimpleNamespace(gameId="game-1"),
            SimpleNamespace(gameId="game-2"),
        ]
        self.game_repository.read_by_column.side_effect = [
            SimpleNamespace(id="game-1"),
            SimpleNamespace(id="game-2"),
        ]
        game_one_detail = SimpleNamespace(
            externalGameId="external-game-1",
            task=[
                SimpleNamespace(
                    externalTaskId="task-external-1",
                    points=[
                        SimpleNamespace(
                            externalUserId="user_1",
                            points=7,
                            timesAwarded=1,
                            pointsData=[
                                {
                                    "points": 7,
                                    "caseName": "rule_1",
                                    "created_at": "2026-02-01T00:00:00",
                                }
                            ],
                        )
                    ],
                )
            ],
        )
        game_two_detail = SimpleNamespace(
            externalGameId="external-game-2",
            task=[
                SimpleNamespace(
                    externalTaskId="task-external-2",
                    points=[
                        SimpleNamespace(
                            externalUserId="user_1",
                            points=5,
                            timesAwarded=2,
                            pointsData=[
                                {
                                    "points": 5,
                                    "caseName": "rule_2",
                                    "created_at": "2026-02-02T00:00:00",
                                }
                            ],
                        )
                    ],
                )
            ],
        )
        self.service.get_points_by_gameId_with_details = MagicMock(
            side_effect=[game_one_detail, game_two_detail]
        )

        result = self.service.get_all_points_by_externalUserId("user_1")

        self.assertEqual(result.points, 12)
        self.assertEqual(result.timesAwarded, 3)
        self.assertEqual(len(result.games), 2)

    def test_extract_points_supports_dict_and_object(self):
        self.assertEqual(UserPointsService._extract_points({"points": 4}), 4)
        self.assertEqual(
            UserPointsService._extract_points(SimpleNamespace(points=7)), 7
        )
        self.assertIsNone(UserPointsService._extract_points({"other": 1}))

    def test_query_user_points_delegates_to_repository(self):
        schema = SimpleNamespace(field="value")
        expected = [SimpleNamespace(id="up-1")]
        self.user_points_repository.read_by_options.return_value = expected

        result = self.service.query_user_points(schema)

        self.assertEqual(result, expected)
        self.user_points_repository.read_by_options.assert_called_once_with(schema)

    def test_get_users_by_game_id_raises_when_game_not_found(self):
        self.game_repository.read_by_column.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_users_by_gameId("missing-game")

    def test_get_users_by_game_id_raises_when_tasks_not_found(self):
        self.game_repository.read_by_column.return_value = SimpleNamespace(id="game-1")
        self.task_repository.read_by_column.return_value = []

        with self.assertRaises(NotFoundError):
            self.service.get_users_by_gameId("game-1")

    def test_get_users_by_game_id_returns_task_users_and_first_action(self):
        self.game_repository.read_by_column.return_value = SimpleNamespace(id="game-1")
        self.task_repository.read_by_column.return_value = [
            SimpleNamespace(id="task-1", externalTaskId="task-ext-1")
        ]
        self.user_points_repository.get_points_and_users_by_taskId.return_value = [
            SimpleNamespace(externalUserId="user_1", userId="user-id-1")
        ]
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            externalUserId="user_1", created_at="2026-01-01T00:00:00"
        )
        self.user_points_repository.get_first_user_points_in_external_task_id_by_user_id.return_value = SimpleNamespace(  # noqa
            created_at="2026-01-02T00:00:00"
        )

        result = self.service.get_users_by_gameId(self.GAME_UUID)

        self.assertEqual(str(result.gameId), self.GAME_UUID)
        self.assertEqual(result.tasks[0].externalTaskId, "task-ext-1")
        self.assertEqual(result.tasks[0].users[0].externalUserId, "user_1")
        self.assertEqual(result.tasks[0].users[0].firstAction, "2026-01-02T00:00:00")

    def test_get_points_by_user_list_aggregates_each_user(self):
        self.service.get_all_points_by_externalUserId = MagicMock(
            side_effect=["result-user-1", "result-user-2"]
        )

        result = self.service.get_points_by_user_list(["user_1", "user_2"])

        self.assertEqual(result, ["result-user-1", "result-user-2"])
        self.assertEqual(
            self.service.get_all_points_by_externalUserId.call_count,
            2,
        )

    def test_get_points_by_external_user_id_raises_when_user_not_found(self):
        self.users_repository.read_by_column.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_points_by_externalUserId("missing_user")

    def test_get_points_by_external_user_id_filters_target_user(self):
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1", externalUserId="user_1"
        )
        self.user_points_repository.get_task_by_externalUserId.return_value = [
            SimpleNamespace(gameId="game-1")
        ]
        self.game_repository.read_by_column.return_value = SimpleNamespace(id="game-1")
        self.service.get_points_by_gameId_with_details = MagicMock(
            return_value=SimpleNamespace(
                externalGameId="external-game-1",
                created_at="2026-01-01T00:00:00",
                task=[
                    SimpleNamespace(
                        externalTaskId="task-ext-1",
                        points=[
                            SimpleNamespace(
                                externalUserId="user_1",
                                points=11,
                                timesAwarded=2,
                                pointsData=[
                                    {
                                        "points": 11,
                                        "caseName": "caseA",
                                        "created_at": "2026-01-01T00:00:00",
                                    }
                                ],
                            ),
                            SimpleNamespace(
                                externalUserId="other-user",
                                points=50,
                                timesAwarded=5,
                                pointsData=[],
                            ),
                        ],
                    )
                ],
            )
        )

        result = self.service.get_points_by_externalUserId("user_1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].externalGameId, "external-game-1")
        self.assertEqual(result[0].task[0].externalTaskId, "task-ext-1")
        self.assertEqual(result[0].task[0].points[0].externalUserId, "user_1")
        self.assertEqual(result[0].task[0].points[0].points, 11)

    def test_get_points_by_game_id_raises_when_tasks_not_found(self):
        self.game_repository.read_by_column.return_value = SimpleNamespace(id="game-1")
        self.task_repository.read_by_column.return_value = []

        with self.assertRaises(NotFoundError):
            self.service.get_points_by_gameId("game-1")

    def test_get_points_by_game_id_returns_points_by_task(self):
        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1",
            externalGameId="external-game-1",
            created_at="2026-01-01T00:00:00",
        )
        self.task_repository.read_by_column.return_value = [
            SimpleNamespace(id="task-1", externalTaskId="task-ext-1")
        ]
        self.user_points_repository.get_points_and_users_by_taskId.return_value = [
            SimpleNamespace(externalUserId="user_1", points=10, timesAwarded=3)
        ]

        result = self.service.get_points_by_gameId("game-1")

        self.assertEqual(result.externalGameId, "external-game-1")
        self.assertEqual(result.task[0].externalTaskId, "task-ext-1")
        self.assertEqual(result.task[0].points[0].points, 10)
        self.assertEqual(result.task[0].points[0].timesAwarded, 3)

    def test_get_points_by_game_id_with_details_returns_points_data(self):
        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1",
            externalGameId="external-game-1",
            created_at="2026-01-01T00:00:00",
        )
        self.task_repository.read_by_column.return_value = [
            SimpleNamespace(id="task-1", externalTaskId="task-ext-1")
        ]
        self.user_points_repository.get_points_and_users_by_taskId.return_value = [
            SimpleNamespace(
                externalUserId="user_1",
                points=10,
                timesAwarded=3,
                pointsData=[
                    {
                        "points": 10,
                        "caseName": "caseA",
                        "created_at": "2026-01-01T00:00:00",
                    }
                ],
            )
        ]

        result = self.service.get_points_by_gameId_with_details("game-1")

        self.assertEqual(result.externalGameId, "external-game-1")
        self.assertEqual(result.task[0].points[0].pointsData[0].caseName, "caseA")

    def test_get_points_of_user_in_game_raises_when_game_not_found(self):
        self.game_repository.read_by_column.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_points_of_user_in_game("missing-game", "user_1")

    def test_get_points_of_user_in_game_raises_when_user_not_found(self):
        self.game_repository.read_by_column.return_value = SimpleNamespace(id="game-1")
        self.users_repository.read_by_column.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.get_points_of_user_in_game("game-1", "missing-user")

    def test_get_points_of_user_in_game_returns_only_target_user_points(self):
        self.game_repository.read_by_column.return_value = SimpleNamespace(id="game-1")
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1", externalUserId="user_1"
        )
        self.task_repository.read_by_column.return_value = [
            SimpleNamespace(id="task-1", externalTaskId="task-ext-1")
        ]
        self.user_points_repository.get_points_and_users_by_taskId.return_value = [
            SimpleNamespace(externalUserId="user_1", points=7, timesAwarded=2),
            SimpleNamespace(externalUserId="user_2", points=100, timesAwarded=10),
        ]

        result = self.service.get_points_of_user_in_game("game-1", "user_1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].externalUserId, "user_1")
        self.assertEqual(result[0].points, 7)

    async def test_assign_points_to_user_directly_creates_user_and_wallet(self):
        self._setup_default_game_task_for_assignment()
        self.service.strategy_service.get_Class_by_id = MagicMock(return_value=object())
        self.users_repository.read_by_column.return_value = None
        self.users_repository.create_user_by_externalUserId = AsyncMock(
            return_value=SimpleNamespace(id="new-user-id", externalUserId="new_user")
        )
        self.user_points_repository.create = AsyncMock(
            return_value=SimpleNamespace(created_at="2026-02-09T00:00:00")
        )
        self.wallet_repository.read_by_column.return_value = None
        self.wallet_repository.create = AsyncMock(
            return_value=SimpleNamespace(id="wallet-1", pointsBalance=3)
        )
        self.wallet_transaction_repository.create = AsyncMock(
            return_value=SimpleNamespace(id="txn-1")
        )

        schema = SimpleNamespace(externalUserId="new_user", data={"points": 3})
        result = await self.service.assign_points_to_user_directly(
            self.GAME_UUID,
            "task-external-1",
            schema,
            "api-key",
        )

        self.assertTrue(result.isACreatedUser)
        self.assertEqual(result.points, 3)
        self.wallet_repository.create.assert_awaited_once()

    async def test_assign_points_to_user_directly_raises_when_task_not_found(self):
        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1", externalGameId="external-game-1"
        )
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = None
        schema = SimpleNamespace(externalUserId="user_1", data={"points": 1})

        with self.assertRaises(NotFoundError):
            await self.service.assign_points_to_user_directly(
                self.GAME_UUID, "missing-task", schema
            )

    async def test_assign_points_to_user_directly_raises_when_strategy_not_found(self):
        self._setup_default_game_task_for_assignment()
        self.service.strategy_service.get_Class_by_id = MagicMock(return_value=None)
        schema = SimpleNamespace(externalUserId="user_1", data={"points": 1})

        with self.assertRaises(NotFoundError):
            await self.service.assign_points_to_user_directly(
                self.GAME_UUID, "task-external-1", schema
            )

    async def test_assign_points_to_user_directly_raises_on_invalid_external_user(self):
        self._setup_default_game_task_for_assignment()
        self.service.strategy_service.get_Class_by_id = MagicMock(return_value=object())
        self.users_repository.read_by_column.return_value = None
        schema = SimpleNamespace(externalUserId="invalid-user!", data={"points": 1})

        with self.assertRaises(PreconditionFailedError):
            await self.service.assign_points_to_user_directly(
                self.GAME_UUID, "task-external-1", schema
            )

    async def test_assign_points_to_user_directly_raises_when_points_missing(self):
        self._setup_default_game_task_for_assignment()
        self.service.strategy_service.get_Class_by_id = MagicMock(return_value=object())
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1", externalUserId="user_1"
        )
        schema = SimpleNamespace(externalUserId="user_1", data={})

        with self.assertRaises(PreconditionFailedError):
            await self.service.assign_points_to_user_directly(
                self.GAME_UUID, "task-external-1", schema
            )

    async def test_assign_points_to_user_directly_raises_when_transaction_missing(self):
        self._setup_default_game_task_for_assignment()
        self.service.strategy_service.get_Class_by_id = MagicMock(return_value=object())
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1", externalUserId="user_1"
        )
        self.user_points_repository.create = AsyncMock(
            return_value=SimpleNamespace(created_at="2026-02-09T00:00:00")
        )
        wallet = SimpleNamespace(id="wallet-1", pointsBalance=10)
        self.wallet_repository.read_by_column.return_value = wallet
        self.wallet_repository.update = AsyncMock(return_value=wallet)
        self.wallet_transaction_repository.create = AsyncMock(return_value=None)
        schema = SimpleNamespace(externalUserId="user_1", data={"points": 2})

        with self.assertRaises(InternalServerError):
            await self.service.assign_points_to_user_directly(
                self.GAME_UUID, "task-external-1", schema, "api-key"
            )

    async def test_assign_points_to_user_success_with_case_name_fallback(self):
        class StrategyWithoutCaseName:
            async def calculate_points(
                self, externalGameId, externalTaskId, externalUserId, data
            ):  # noqa
                return (9, None, {"foo": "bar"})

        self._setup_default_game_task_for_assignment()
        self.service.strategy_service.get_strategy_by_id = MagicMock(
            return_value=object()
        )
        self.service.strategy_service.get_Class_by_id = MagicMock(
            return_value=StrategyWithoutCaseName()
        )
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1", externalUserId="user_1"
        )
        self.user_points_repository.create = AsyncMock(
            return_value=SimpleNamespace(created_at="2026-02-09T00:00:00")
        )
        self.wallet_repository.read_by_column.return_value = None
        self.wallet_repository.create = AsyncMock(
            return_value=SimpleNamespace(id="wallet-1", pointsBalance=9)
        )
        self.wallet_transaction_repository.create = AsyncMock(
            return_value=SimpleNamespace(id="txn-1")
        )
        schema = SimpleNamespace(externalUserId="user_1", data={}, caseName="fallback")

        result = await self.service.assign_points_to_user(
            self.GAME_UUID, "task-external-1", schema, False, "api-key"
        )

        self.assertEqual(result.points, 9)
        self.assertEqual(result.caseName, "fallback")
        self.assertIn("callbackData", schema.data)
        self.wallet_repository.create.assert_awaited_once()

    async def test_assign_points_to_user_raises_when_strategy_metadata_missing(self):
        self._setup_default_game_task_for_assignment()
        self.service.strategy_service.get_strategy_by_id = MagicMock(return_value=None)
        schema = SimpleNamespace(externalUserId="user_1", data={})

        with self.assertRaises(NotFoundError):
            await self.service.assign_points_to_user(
                self.GAME_UUID, "task-external-1", schema
            )

    async def test_assign_points_to_user_raises_when_points_minus_one(self):
        class StrategyFailWithMinusOne:
            async def calculate_points(
                self, externalGameId, externalTaskId, externalUserId, data
            ):  # noqa
                return (-1, "rule_failed", None)

        self._setup_default_game_task_for_assignment()
        self.service.strategy_service.get_strategy_by_id = MagicMock(
            return_value=object()
        )
        self.service.strategy_service.get_Class_by_id = MagicMock(
            return_value=StrategyFailWithMinusOne()
        )
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1", externalUserId="user_1"
        )
        schema = SimpleNamespace(externalUserId="user_1", data={})

        with self.assertRaises(PreconditionFailedError):
            await self.service.assign_points_to_user(
                self.GAME_UUID, "task-external-1", schema
            )

    async def test_assign_points_to_user_raises_when_points_none(self):
        class StrategyWithNoPoints:
            async def calculate_points(
                self, externalGameId, externalTaskId, externalUserId, data
            ):  # noqa
                return (None, "caseA", None)

        self._setup_default_game_task_for_assignment()
        self.service.strategy_service.get_strategy_by_id = MagicMock(
            return_value=object()
        )
        self.service.strategy_service.get_Class_by_id = MagicMock(
            return_value=StrategyWithNoPoints()
        )
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1", externalUserId="user_1"
        )
        schema = SimpleNamespace(externalUserId="user_1", data={})

        with self.assertRaises(InternalServerError):
            await self.service.assign_points_to_user(
                self.GAME_UUID, "task-external-1", schema
            )

    async def test_assign_points_to_user_raises_when_strategy_calculation_crashes(self):
        class CrashingStrategy:
            async def calculate_points(
                self, externalGameId, externalTaskId, externalUserId, data
            ):  # noqa
                raise RuntimeError("unexpected")

        self._setup_default_game_task_for_assignment()
        self.service.strategy_service.get_strategy_by_id = MagicMock(
            return_value=object()
        )
        self.service.strategy_service.get_Class_by_id = MagicMock(
            return_value=CrashingStrategy()
        )
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1", externalUserId="user_1"
        )
        schema = SimpleNamespace(externalUserId="user_1", data={})

        with self.assertRaises(InternalServerError):
            await self.service.assign_points_to_user(
                self.GAME_UUID, "task-external-1", schema
            )

    async def test_get_points_simulated_of_user_in_game_raises_when_tasks_not_found(
        self,
    ):
        self.game_repository.read_by_column.return_value = SimpleNamespace(id="game-1")
        self.task_repository.read_by_column.return_value = []

        with self.assertRaises(NotFoundError):
            await self.service.get_points_simulated_of_user_in_game("game-1", "user_1")

    async def test_get_points_simulated_of_user_in_game_raises_when_strategy_missing(
        self,
    ):
        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1", externalGameId="external-game-1"
        )
        self.task_repository.read_by_column.return_value = [
            SimpleNamespace(id="task-1", strategyId="strategy-1", externalTaskId="t-1")
        ]
        self.service.strategy_service.get_strategy_by_id = MagicMock(return_value=None)

        with self.assertRaises(NotFoundError):
            await self.service.get_points_simulated_of_user_in_game("game-1", "user_1")

    async def test_get_points_simulated_of_user_in_game_raises_for_invalid_user_slug(
        self,
    ):
        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1", externalGameId="external-game-1"
        )
        self.task_repository.read_by_column.return_value = [
            SimpleNamespace(id="task-1", strategyId="strategy-1", externalTaskId="t-1")
        ]
        self.service.strategy_service.get_strategy_by_id = MagicMock(
            return_value=object()
        )
        self.users_repository.read_by_column.return_value = None

        with self.assertRaises(PreconditionFailedError):
            await self.service.get_points_simulated_of_user_in_game(
                "game-1", "invalid-user!"
            )

    async def test_get_points_simulated_of_user_in_game_assigns_control_group(self):
        class SimStrategy:
            def simulate_strategy(self, data_to_simulate, userGroup, user_last_task):
                return {
                    "externalTaskId": data_to_simulate["task"].externalTaskId,
                    "group": userGroup,
                    "hasLastTask": user_last_task is not None,
                }

        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1", externalGameId="external-game-1"
        )
        self.task_repository.read_by_column.return_value = [
            SimpleNamespace(id="task-1", strategyId="strategy-1", externalTaskId="t-1"),
            SimpleNamespace(id="task-2", strategyId="strategy-1", externalTaskId="t-2"),
        ]
        self.service.strategy_service.get_strategy_by_id = MagicMock(
            return_value=object()
        )
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1", externalUserId="user_1"
        )
        self.users_game_config_repository.read_by_columns.return_value = None
        self.users_game_config_repository.get_all_users_by_gameId.return_value = [
            SimpleNamespace(experimentGroup="random_range"),
            SimpleNamespace(experimentGroup="average_score"),
        ]
        self.users_game_config_repository.create = AsyncMock(
            return_value=SimpleNamespace(experimentGroup="dynamic_calculation")
        )
        self.user_points_repository.get_last_task_by_userId.return_value = (
            SimpleNamespace(id="last-task")
        )
        self.service.strategy_service.get_Class_by_id = MagicMock(
            return_value=SimStrategy()
        )

        result, external_game_id = (
            await self.service.get_points_simulated_of_user_in_game(
                "game-1",
                "user_1",
                assign_control_group=True,
            )
        )

        self.assertEqual(external_game_id, "external-game-1")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["group"], "dynamic_calculation")
        self.users_game_config_repository.create.assert_awaited_once()

    async def test_get_points_simulated_of_user_in_game_raises_when_simulate_missing(
        self,
    ):
        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1", externalGameId="external-game-1"
        )
        self.task_repository.read_by_column.return_value = [
            SimpleNamespace(id="task-1", strategyId="strategy-1", externalTaskId="t-1")
        ]
        self.service.strategy_service.get_strategy_by_id = MagicMock(
            return_value=object()
        )
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1", externalUserId="user_1"
        )
        self.user_points_repository.get_last_task_by_userId.return_value = None
        self.service.strategy_service.get_Class_by_id = MagicMock(return_value=object())

        with self.assertRaises(NotFoundError):
            await self.service.get_points_simulated_of_user_in_game("game-1", "user_1")

    async def test_get_points_simulated_of_user_in_game_logs_and_continues_on_exception(
        self,
    ):
        class FailingSimulationStrategy:
            def simulate_strategy(self, data_to_simulate, userGroup, user_last_task):
                raise RuntimeError("sim error")

        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1", externalGameId="external-game-1"
        )
        self.task_repository.read_by_column.return_value = [
            SimpleNamespace(id="task-1", strategyId="strategy-1", externalTaskId="t-1")
        ]
        self.service.strategy_service.get_strategy_by_id = MagicMock(
            return_value=object()
        )
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1", externalUserId="user_1"
        )
        self.user_points_repository.get_last_task_by_userId.return_value = None
        self.service.strategy_service.get_Class_by_id = MagicMock(
            return_value=FailingSimulationStrategy()
        )

        result, external_game_id = (
            await self.service.get_points_simulated_of_user_in_game(
                "game-1",
                "user_1",
            )
        )

        self.assertEqual(result, [])
        self.assertEqual(external_game_id, "external-game-1")

    def test_get_users_points_by_external_game_id_raises_when_game_has_no_tasks(self):
        self.game_repository.read_by_column.return_value = SimpleNamespace(id="game-1")
        self.task_repository.read_by_column.return_value = []

        with self.assertRaises(NotFoundError):
            self.service.get_users_points_by_externalGameId("external-game-1")

    def test_get_users_points_by_external_task_id_returns_points(self):
        self.task_repository.read_by_column.return_value = SimpleNamespace(id="task-1")
        self.user_points_repository.get_points_and_users_by_taskId.return_value = [
            SimpleNamespace(externalUserId="user_1", points=1),
            SimpleNamespace(externalUserId="user_2", points=2),
        ]

        result = self.service.get_users_points_by_externalTaskId("task-ext-1")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].externalUserId, "user_1")
        self.assertEqual(result[1].points, 2)

    def test_get_users_points_by_external_task_id_and_user_id_delegates(self):
        self.task_repository.read_by_column.return_value = SimpleNamespace(id="task-1")
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1"
        )
        expected = [SimpleNamespace(points=5)]
        self.user_points_repository.read_by_columns.return_value = expected

        result = self.service.get_users_points_by_externalTaskId_and_externalUserId(
            "task-ext-1", "user_1"
        )

        self.assertEqual(result, expected)
        self.user_points_repository.read_by_columns.assert_called_once_with(
            {"taskId": "task-1", "userId": "user-id-1"}
        )

    def test_get_all_points_by_external_user_id_returns_empty_when_user_missing(self):
        self.users_repository.read_by_column.return_value = None

        result = self.service.get_all_points_by_externalUserId("missing-user")

        self.assertEqual(result.externalUserId, "missing-user")
        self.assertEqual(result.points, 0)
        self.assertEqual(result.timesAwarded, 0)
        self.assertEqual(result.games, [])
        self.assertFalse(result.userExists)

    def test_get_points_of_user_sums_points(self):
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-id-1"
        )
        self.user_points_repository.get_task_and_sum_points_by_userId.return_value = [
            PointsByUserInTask(externalTaskId="task-ext-1", points=4),
            PointsByUserInTask(externalTaskId="task-ext-2", points=6),
        ]

        result = self.service.get_points_of_user("user_1")

        self.assertEqual(result.externalUserId, "user_1")
        self.assertEqual(result.points, 10)
        self.assertEqual(len(result.points_by_task), 2)

    def test_repository_passthrough_methods_delegate_and_return(self):
        self.user_points_repository.count_measurements_by_external_task_id.return_value = (
            5
        )
        self.user_points_repository.get_user_task_measurements_count.return_value = 2
        self.user_points_repository.get_user_task_measurements_count_the_last_seconds.return_value = (  # noqa
            1
        )
        self.user_points_repository.get_avg_time_between_tasks_by_user_and_game_task.return_value = (  # noqa
            10.5
        )
        self.user_points_repository.get_avg_time_between_tasks_for_all_users.return_value = (
            8.2
        )
        self.user_points_repository.get_last_window_time_diff.return_value = 4
        self.user_points_repository.get_new_last_window_time_diff.return_value = 6
        self.user_points_repository.get_user_task_measurements.return_value = [
            {"minutes": 5}
        ]
        self.user_points_repository.count_personal_records_by_external_game_id.return_value = (
            7
        )
        self.user_points_repository.user_has_record_before_in_externalTaskId_last_min.return_value = (  # noqa
            True
        )
        self.user_points_repository.get_global_avg_by_external_game_id.return_value = (
            12.3
        )
        self.user_points_repository.get_personal_avg_by_external_game_id.return_value = (
            9.9
        )
        self.user_points_repository.get_points_of_simulated_task.return_value = [
            {"points": 1}
        ]
        self.user_points_repository.get_all_point_of_tasks_list.return_value = [
            {"taskId": "task-1"}
        ]

        self.assertEqual(self.service.count_measurements_by_external_task_id("task"), 5)
        self.assertEqual(
            self.service.get_user_task_measurements_count("task", "user"),
            2,
        )
        self.assertEqual(
            self.service.get_user_task_measurements_count_the_last_seconds(
                "task", "user", 60
            ),
            1,
        )
        self.assertEqual(
            self.service.get_avg_time_between_tasks_by_user_and_game_task(
                "game", "task", "user"
            ),
            10.5,
        )
        self.assertEqual(
            self.service.get_avg_time_between_tasks_for_all_users("game", "task"),
            8.2,
        )
        self.assertEqual(self.service.get_last_window_time_diff("task", "user"), 4)
        self.assertEqual(
            self.service.get_new_last_window_time_diff("task", "user", "game"),
            6,
        )
        self.assertEqual(
            self.service.get_user_task_measurements("task", "user"),
            [{"minutes": 5}],
        )
        self.assertEqual(
            self.service.count_personal_records_by_external_game_id("game", "user"),
            7,
        )
        self.assertTrue(
            self.service.user_has_record_before_in_externalTaskId_last_min(
                "task",
                "user",
                5,
            )
        )
        self.assertEqual(self.service.get_global_avg_by_external_game_id("game"), 12.3)
        self.assertEqual(
            self.service.get_personal_avg_by_external_game_id("game", "user"), 9.9
        )
        self.assertEqual(
            self.service.get_points_of_simulated_task("task", "hash"),
            [{"points": 1}],
        )
        self.assertEqual(
            self.service.get_all_point_of_tasks_list(["task-1"], withData=True),
            [{"taskId": "task-1"}],
        )


if __name__ == "__main__":
    unittest.main()
