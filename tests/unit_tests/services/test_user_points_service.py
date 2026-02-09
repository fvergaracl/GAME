import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import InternalServerError
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
            async def calculate_points(self, externalGameId, externalTaskId, externalUserId, data):  # noqa
                return (5, None, None)

        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1", externalGameId="external-game-1"
        )
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = (
            SimpleNamespace(id="task-1", strategyId="default")
        )
        self.service.strategy_service.get_strategy_by_id = MagicMock(return_value=object())
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


if __name__ == "__main__":
    unittest.main()
