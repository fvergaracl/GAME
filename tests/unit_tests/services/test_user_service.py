import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.repository.wallet_repository import WalletRepository
from app.repository.wallet_transaction_repository import WalletTransactionRepository
from app.schema.user_points_schema import BaseUserPointsBaseModelWithCaseName
from app.schema.user_schema import PostPointsConversionRequest
from app.schema.wallet_schema import WalletWithoutUserId
from app.schema.wallet_transaction_schema import BaseWalletTransactionInfo
from app.services.user_service import UserService


class WalletModel(WalletWithoutUserId):
    id: str
    updated_at: datetime


class MeasurementCountEqualTwoOnly:
    def __le__(self, other):
        return False

    def __eq__(self, other):
        return other == 2


class ComparableDuration:
    def __init__(self, ge_value, lt_value, gt_value):
        self.ge_value = ge_value
        self.lt_value = lt_value
        self.gt_value = gt_value

    def __ge__(self, other):
        return self.ge_value

    def __lt__(self, other):
        return self.lt_value

    def __gt__(self, other):
        return self.gt_value


class FakeDurationValue:
    def __init__(self, comparable_duration):
        self.comparable_duration = comparable_duration

    def __truediv__(self, other):
        return self.comparable_duration


class FakeTimedelta:
    def __init__(self, comparable_duration):
        self.comparable_duration = comparable_duration

    def total_seconds(self):
        return FakeDurationValue(self.comparable_duration)


class FakeEndTime:
    def __init__(self, comparable_duration):
        self.comparable_duration = comparable_duration

    def __sub__(self, other):
        return FakeTimedelta(self.comparable_duration)


class TestUserService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user_repository = MagicMock(spec=UserRepository)
        self.user_points_repository = MagicMock(spec=UserPointsRepository)
        self.task_repository = MagicMock(spec=TaskRepository)
        self.wallet_repository = MagicMock(spec=WalletRepository)
        self.wallet_transaction_repository = MagicMock(spec=WalletTransactionRepository)
        self.service = UserService(
            user_repository=self.user_repository,
            user_points_repository=self.user_points_repository,
            task_repository=self.task_repository,
            wallet_repository=self.wallet_repository,
            wallet_transaction_repository=self.wallet_transaction_repository,
        )

    def _setup_assign_points_default_mocks(
        self,
        user,
        measurement_count,
        start_time_last_task,
        end_time_last_task,
        individual_calculation,
        global_calculation,
    ):
        self.user_repository.read_by_id.return_value = user
        self.user_points_repository.get_user_measurement_count.return_value = (
            measurement_count
        )
        self.user_points_repository.get_start_time_for_last_task.return_value = (
            start_time_last_task
        )
        self.user_points_repository.get_time_taken_for_last_task.return_value = (
            end_time_last_task
        )
        self.user_points_repository.get_individual_calculation.return_value = (
            individual_calculation
        )
        self.user_points_repository.get_global_calculation.return_value = global_calculation
        self.user_points_repository.create = AsyncMock(
            side_effect=lambda user_points_schema: SimpleNamespace(
                id=uuid4(),
                caseName=user_points_schema.caseName,
                created_at=datetime(2026, 1, 1, 10, 0, 0),
                updated_at=datetime(2026, 1, 1, 10, 1, 0),
                description=user_points_schema.description,
                userId=user_points_schema.userId,
                taskId=user_points_schema.taskId,
                points=user_points_schema.points,
                data=user_points_schema.data,
            )
        )
        wallet = WalletModel(
            id=str(uuid4()),
            coinsBalance=0,
            pointsBalance=100,
            conversionRate=100,
            updated_at=datetime(2026, 1, 1, 10, 2, 0),
        )
        self.wallet_repository.read_by_column.return_value = wallet
        self.wallet_repository.update = AsyncMock(return_value=wallet)
        self.wallet_transaction_repository.create = AsyncMock(return_value=SimpleNamespace())

    def test_helper_points_methods_and_create_user(self):
        self.assertEqual(self.service.basic_engagement_points(), 1)
        self.assertEqual(self.service.performance_penalty_points(), -5)
        self.assertEqual(self.service.performance_bonus_points(), 10)
        self.assertEqual(self.service.individual_over_global_points(), 5)
        self.assertEqual(self.service.need_for_motivation_points(), 2)
        self.assertEqual(self.service.peak_performer_bonus_points(), 15)
        self.assertEqual(self.service.global_advantage_adjustment_points(), 7)
        self.assertEqual(self.service.individual_adjustment_points(), 8)

    async def test_create_user_delegates_to_repository(self):
        schema = {"externalUserId": "user_1"}
        self.user_repository.create = AsyncMock(return_value={"id": "u1"})
        result = await self.service.create_user(schema)
        self.user_repository.create.assert_called_once_with(schema)
        self.assertEqual(result, {"id": "u1"})

    async def test_assign_points_to_user_basic_engagement_creates_wallet(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_id.return_value = user
        self.user_points_repository.get_user_measurement_count.return_value = 1
        self.user_points_repository.get_start_time_for_last_task.return_value = None
        self.user_points_repository.get_time_taken_for_last_task.return_value = None
        self.user_points_repository.get_individual_calculation.return_value = 10
        self.user_points_repository.get_global_calculation.return_value = 8
        created_user_points = SimpleNamespace(
            id=uuid4(),
            caseName="CaseA",
            created_at=datetime(2026, 1, 1, 10, 0, 0),
            updated_at=datetime(2026, 1, 1, 10, 1, 0),
            description="desc",
            userId=user.id,
            taskId="task-1",
            points=1,
            data={"label_function_choose": "basic_engagement_points"},
        )
        self.user_points_repository.create = AsyncMock(return_value=created_user_points)
        self.wallet_repository.read_by_column.return_value = None
        new_wallet = WalletModel(
            id="wallet-1",
            coinsBalance=0,
            pointsBalance=1,
            conversionRate=100,
            updated_at=datetime(2026, 1, 1, 10, 2, 0),
        )
        self.wallet_repository.create = AsyncMock(return_value=new_wallet)
        self.wallet_transaction_repository.create = AsyncMock(return_value=SimpleNamespace())

        schema = BaseUserPointsBaseModelWithCaseName(
            userId=str(user.id),
            taskId="task-1",
            caseName="CaseA",
            points=0,
            description="desc",
            data={},
        )
        response = await self.service.assign_points_to_user(str(user.id), schema, "api-key")

        self.assertEqual(response.points, 1)
        self.assertEqual(response.caseName, "CaseA")
        self.assertEqual(response.wallet.pointsBalance, 1)
        self.assertEqual(schema.data["label_function_choose"], "basic_engagement_points")
        self.wallet_repository.create.assert_awaited_once()
        self.wallet_transaction_repository.create.assert_awaited_once()

    async def test_assign_points_to_user_updates_existing_wallet_when_points_present(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_id.return_value = user
        self.user_points_repository.get_user_measurement_count.return_value = 10
        self.user_points_repository.get_start_time_for_last_task.return_value = None
        self.user_points_repository.get_time_taken_for_last_task.return_value = None
        self.user_points_repository.get_individual_calculation.return_value = 10
        self.user_points_repository.get_global_calculation.return_value = 8
        created_user_points = SimpleNamespace(
            id=uuid4(),
            caseName="CaseB",
            created_at=datetime(2026, 1, 1, 10, 0, 0),
            updated_at=datetime(2026, 1, 1, 10, 1, 0),
            description="desc",
            userId=user.id,
            taskId="task-1",
            points=5,
            data={"label_function_choose": "-"},
        )
        self.user_points_repository.create = AsyncMock(return_value=created_user_points)
        wallet = WalletModel(
            id="wallet-2",
            coinsBalance=2,
            pointsBalance=10,
            conversionRate=100,
            updated_at=datetime(2026, 1, 1, 10, 2, 0),
        )
        self.wallet_repository.read_by_column.return_value = wallet
        self.wallet_repository.update = AsyncMock(return_value=wallet)
        self.wallet_transaction_repository.create = AsyncMock(return_value=SimpleNamespace())

        schema = BaseUserPointsBaseModelWithCaseName(
            userId=str(user.id),
            taskId="task-1",
            caseName="CaseB",
            points=5,
            description="desc",
            data={},
        )
        response = await self.service.assign_points_to_user(str(user.id), schema, "api-key")

        self.assertEqual(response.points, 5)
        self.assertEqual(response.wallet.pointsBalance, 15)
        self.assertEqual(schema.data["label_function_choose"], "-")
        self.wallet_repository.update.assert_awaited_once()
        self.wallet_repository.create.assert_not_called()

    async def test_assign_points_to_user_need_for_motivation_branch(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_id.return_value = user
        self.user_points_repository.get_user_measurement_count.return_value = 3
        start = datetime(2026, 1, 1, 10, 0, 0)
        end = start + timedelta(minutes=12)
        self.user_points_repository.get_start_time_for_last_task.return_value = start
        self.user_points_repository.get_time_taken_for_last_task.return_value = end
        self.user_points_repository.get_individual_calculation.return_value = 10
        self.user_points_repository.get_global_calculation.return_value = 8
        created_user_points = SimpleNamespace(
            id=uuid4(),
            caseName="CaseC",
            created_at=datetime(2026, 1, 1, 10, 0, 0),
            updated_at=datetime(2026, 1, 1, 10, 1, 0),
            description="desc",
            userId=user.id,
            taskId="task-1",
            points=2,
            data={"label_function_choose": "need_for_motivation_points"},
        )
        self.user_points_repository.create = AsyncMock(return_value=created_user_points)
        wallet = WalletModel(
            id="wallet-3",
            coinsBalance=0,
            pointsBalance=20,
            conversionRate=100,
            updated_at=datetime(2026, 1, 1, 10, 2, 0),
        )
        self.wallet_repository.read_by_column.return_value = wallet
        self.wallet_repository.update = AsyncMock(return_value=wallet)
        self.wallet_transaction_repository.create = AsyncMock(return_value=SimpleNamespace())

        schema = BaseUserPointsBaseModelWithCaseName(
            userId=str(user.id),
            taskId="task-1",
            caseName="CaseC",
            points=0,
            description="desc",
            data={},
        )
        await self.service.assign_points_to_user(str(user.id), schema, "api-key")

        self.assertEqual(schema.data["label_function_choose"], "need_for_motivation_points")

    async def test_assign_points_to_user_individual_adjustment_branch(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_id.return_value = user
        self.user_points_repository.get_user_measurement_count.return_value = 3
        start = datetime(2026, 1, 1, 10, 0, 0)
        end = start + timedelta(minutes=2)
        self.user_points_repository.get_start_time_for_last_task.return_value = start
        self.user_points_repository.get_time_taken_for_last_task.return_value = end
        self.user_points_repository.get_individual_calculation.return_value = 5
        self.user_points_repository.get_global_calculation.return_value = 3
        created_user_points = SimpleNamespace(
            id=uuid4(),
            caseName="CaseD",
            created_at=datetime(2026, 1, 1, 10, 0, 0),
            updated_at=datetime(2026, 1, 1, 10, 1, 0),
            description="desc",
            userId=user.id,
            taskId="task-1",
            points=8,
            data={"label_function_choose": "individual_adjustment_points"},
        )
        self.user_points_repository.create = AsyncMock(return_value=created_user_points)
        wallet = WalletModel(
            id="wallet-4",
            coinsBalance=0,
            pointsBalance=30,
            conversionRate=100,
            updated_at=datetime(2026, 1, 1, 10, 2, 0),
        )
        self.wallet_repository.read_by_column.return_value = wallet
        self.wallet_repository.update = AsyncMock(return_value=wallet)
        self.wallet_transaction_repository.create = AsyncMock(return_value=SimpleNamespace())

        schema = BaseUserPointsBaseModelWithCaseName(
            userId=str(user.id),
            taskId="task-1",
            caseName="CaseD",
            points=0,
            description="desc",
            data={},
        )
        await self.service.assign_points_to_user(str(user.id), schema, "api-key")

        self.assertEqual(schema.data["label_function_choose"], "individual_adjustment_points")

    async def test_assign_points_to_user_performance_penalty_branch(self):
        user = SimpleNamespace(id=uuid4())
        start = datetime(2026, 1, 1, 10, 0, 0)
        end = start + timedelta(minutes=15)
        self._setup_assign_points_default_mocks(
            user=user,
            measurement_count=MeasurementCountEqualTwoOnly(),
            start_time_last_task=start,
            end_time_last_task=end,
            individual_calculation=10,
            global_calculation=5,
        )
        schema = BaseUserPointsBaseModelWithCaseName(
            userId=str(user.id),
            taskId="task-1",
            caseName="CasePenalty",
            points=0,
            description="desc",
            data={},
        )

        response = await self.service.assign_points_to_user(str(user.id), schema, "api-key")

        self.assertEqual(response.points, -5)
        self.assertEqual(schema.data["label_function_choose"], "performance_penalty_points")

    async def test_assign_points_to_user_performance_bonus_branch(self):
        user = SimpleNamespace(id=uuid4())
        start = datetime(2026, 1, 1, 10, 0, 0)
        end = start + timedelta(minutes=5)
        self._setup_assign_points_default_mocks(
            user=user,
            measurement_count=MeasurementCountEqualTwoOnly(),
            start_time_last_task=start,
            end_time_last_task=end,
            individual_calculation=10,
            global_calculation=30,
        )
        schema = BaseUserPointsBaseModelWithCaseName(
            userId=str(user.id),
            taskId="task-1",
            caseName="CaseBonus",
            points=0,
            description="desc",
            data={},
        )

        response = await self.service.assign_points_to_user(str(user.id), schema, "api-key")

        self.assertEqual(response.points, 10)
        self.assertEqual(schema.data["label_function_choose"], "performance_bonus_points")

    async def test_assign_points_to_user_individual_over_global_unreachable_branch(self):
        user = SimpleNamespace(id=uuid4())
        comparable_duration = ComparableDuration(ge_value=True, lt_value=True, gt_value=True)
        self._setup_assign_points_default_mocks(
            user=user,
            measurement_count=3,
            start_time_last_task=object(),
            end_time_last_task=FakeEndTime(comparable_duration),
            individual_calculation=10,
            global_calculation=5,
        )
        schema = BaseUserPointsBaseModelWithCaseName(
            userId=str(user.id),
            taskId="task-1",
            caseName="CaseIOG",
            points=0,
            description="desc",
            data={},
        )

        response = await self.service.assign_points_to_user(str(user.id), schema, "api-key")

        self.assertEqual(response.points, 5)
        self.assertEqual(
            schema.data["label_function_choose"], "individual_over_global_points"
        )

    async def test_assign_points_to_user_peak_performer_unreachable_branch(self):
        user = SimpleNamespace(id=uuid4())
        comparable_duration = ComparableDuration(ge_value=True, lt_value=True, gt_value=False)
        self._setup_assign_points_default_mocks(
            user=user,
            measurement_count=3,
            start_time_last_task=object(),
            end_time_last_task=FakeEndTime(comparable_duration),
            individual_calculation=10,
            global_calculation=5,
        )
        schema = BaseUserPointsBaseModelWithCaseName(
            userId=str(user.id),
            taskId="task-1",
            caseName="CasePeak",
            points=0,
            description="desc",
            data={},
        )

        response = await self.service.assign_points_to_user(str(user.id), schema, "api-key")

        self.assertEqual(response.points, 15)
        self.assertEqual(schema.data["label_function_choose"], "peak_performer_bonus_points")

    async def test_assign_points_to_user_global_advantage_adjustment_else_branch(self):
        user = SimpleNamespace(id=uuid4())
        comparable_duration = ComparableDuration(ge_value=True, lt_value=False, gt_value=False)
        self._setup_assign_points_default_mocks(
            user=user,
            measurement_count=3,
            start_time_last_task=object(),
            end_time_last_task=FakeEndTime(comparable_duration),
            individual_calculation=10,
            global_calculation=5,
        )
        schema = BaseUserPointsBaseModelWithCaseName(
            userId=str(user.id),
            taskId="task-1",
            caseName="CaseGlobalAdj",
            points=0,
            description="desc",
            data={},
        )

        response = await self.service.assign_points_to_user(str(user.id), schema, "api-key")

        self.assertEqual(response.points, 7)
        self.assertEqual(
            schema.data["label_function_choose"], "global_advantage_adjustment_points"
        )

    async def test_get_wallet_by_user_id_creates_wallet_when_missing(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_id.return_value = user
        self.wallet_repository.read_by_column.return_value = None
        wallet = WalletModel(
            id="wallet-5",
            coinsBalance=0,
            pointsBalance=0,
            conversionRate=100,
            updated_at=datetime(2026, 1, 1, 10, 2, 0),
        )
        self.wallet_repository.create = AsyncMock(return_value=wallet)
        tx = BaseWalletTransactionInfo(
            id=uuid4(),
            transactionType="AssignPoints",
            points=10,
            coins=0,
            data={},
            created_at="placeholder",
        )
        tx.created_at = datetime(2026, 1, 1, 10, 3, 0)
        self.wallet_transaction_repository.read_by_column.return_value = [tx]

        response = await self.service.get_wallet_by_user_id(str(user.id))

        self.assertEqual(response.userId, str(user.id))
        self.assertEqual(response.wallet.pointsBalance, 0)
        self.assertEqual(len(response.walletTransactions), 1)
        self.assertIsInstance(response.walletTransactions[0].created_at, str)
        self.wallet_repository.create.assert_awaited_once()

    async def test_get_wallet_by_external_user_id_delegates(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_column.return_value = user
        expected_response = {"wallet": "ok"}
        self.service.get_wallet_by_user_id = AsyncMock(return_value=expected_response)

        result = await self.service.get_wallet_by_externalUserId("external-user")

        self.assertEqual(result, expected_response)
        self.service.get_wallet_by_user_id.assert_awaited_once_with(str(user.id))

    def test_get_user_by_external_user_id(self):
        expected_user = {"id": "u1"}
        self.user_repository.read_by_column.return_value = expected_user

        result = self.service.get_user_by_externalUserId("external-user")

        self.user_repository.read_by_column.assert_called_once_with(
            "externalUserId", "external-user", not_found_raise_exception=False
        )
        self.assertEqual(result, expected_user)

    def test_get_points_by_user_id_returns_empty_tasks(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_id.return_value = user
        self.user_points_repository.read_by_column.return_value = []

        result = self.service.get_points_by_user_id(str(user.id))

        self.assertEqual(str(result.id), str(user.id))
        self.assertEqual(result.tasks, [])

    def test_get_points_by_user_id_returns_cleaned_tasks(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_id.return_value = user
        self.user_points_repository.read_by_column.return_value = [
            SimpleNamespace(taskId="task-1", userId=user.id),
            SimpleNamespace(taskId="task-1", userId=user.id),
        ]
        self.task_repository.read_by_id.return_value = SimpleNamespace(
            id="task-1", externalTaskId="external-task-1", gameId="game-1"
        )
        self.user_points_repository.get_points_and_users_by_taskId.return_value = [
            SimpleNamespace(userId=str(user.id), points=11),
            SimpleNamespace(userId="other-user", points=3),
        ]

        result = self.service.get_points_by_user_id(str(user.id))

        self.assertEqual(len(result.tasks), 1)
        self.assertEqual(result.tasks[0].taskId, "task-1")
        self.assertEqual(result.tasks[0].points, 11)

    def test_preview_points_to_coins_conversion_validates_points(self):
        with self.assertRaises(ValueError):
            self.service.preview_points_to_coins_conversion("user-1", 0)
        with self.assertRaises(ValueError):
            self.service.preview_points_to_coins_conversion("user-1", -1)

    def test_preview_points_to_coins_conversion_creates_wallet_when_missing(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_id.return_value = user
        self.wallet_repository.read_by_column.return_value = None
        wallet = SimpleNamespace(
            id="wallet-6",
            coinsBalance=1.0,
            pointsBalance=5.0,
            conversionRate=10.0,
            updated_at=datetime(2026, 1, 1, 10, 0, 0),
        )
        self.wallet_repository.create = MagicMock(return_value=wallet)

        result = self.service.preview_points_to_coins_conversion(str(user.id), 20)

        self.assertEqual(result["points"], 20)
        self.assertEqual(result["conversionRate"], 10.0)
        self.assertEqual(result["convertedAmount"], 2.0)
        self.assertFalse(result["haveEnoughPoints"])
        self.wallet_repository.create.assert_called_once()

    def test_preview_points_to_coins_conversion_external_user_id_delegates(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_column.return_value = user
        self.service.preview_points_to_coins_conversion = MagicMock(
            return_value={"convertedAmount": 1.0}
        )

        result = self.service.preview_points_to_coins_conversion_externalUserId(
            "external-user", 10
        )

        self.assertEqual(result["convertedAmount"], 1.0)
        self.service.preview_points_to_coins_conversion.assert_called_once_with(
            str(user.id), 10
        )

    async def test_convert_points_to_coins_validates_points(self):
        with self.assertRaises(ValueError):
            await self.service.convert_points_to_coins(
                "user-1", PostPointsConversionRequest(points=0), "api-key"
            )
        with self.assertRaises(ValueError):
            await self.service.convert_points_to_coins(
                "user-1", PostPointsConversionRequest(points=-1), "api-key"
            )

    async def test_convert_points_to_coins_raises_when_not_enough_points(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_id.return_value = user
        wallet = SimpleNamespace(
            id="wallet-7",
            coinsBalance=1.0,
            pointsBalance=5.0,
            conversionRate=10.0,
            updated_at=datetime(2026, 1, 1, 10, 0, 0),
        )
        self.wallet_repository.read_by_column = AsyncMock(return_value=wallet)
        self.wallet_repository.update = AsyncMock()

        with self.assertRaises(ValueError):
            await self.service.convert_points_to_coins(
                str(user.id), PostPointsConversionRequest(points=20), "api-key"
            )

        self.wallet_repository.update.assert_not_awaited()

    async def test_convert_points_to_coins_success(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_id.return_value = user
        wallet = SimpleNamespace(
            id="wallet-8",
            coinsBalance=5.0,
            pointsBalance=100.0,
            conversionRate=10.0,
            updated_at=datetime(2026, 1, 1, 10, 0, 0),
        )
        self.wallet_repository.read_by_column = AsyncMock(return_value=wallet)
        self.wallet_repository.update = AsyncMock(return_value=wallet)
        self.wallet_transaction_repository.create = MagicMock(
            return_value=SimpleNamespace(id=uuid4())
        )

        response = await self.service.convert_points_to_coins(
            str(user.id), PostPointsConversionRequest(points=20), "api-key"
        )

        self.assertEqual(response.points, 20)
        self.assertEqual(response.convertedAmount, 2.0)
        self.assertEqual(response.convertedCurrency, "coins")
        self.assertTrue(response.haveEnoughPoints)
        self.assertEqual(wallet.pointsBalance, 80.0)
        self.assertEqual(wallet.coinsBalance, 7.0)
        self.wallet_repository.update.assert_awaited_once_with(wallet.id, wallet)
        self.wallet_transaction_repository.create.assert_called_once()

    async def test_convert_points_to_coins_creates_wallet_when_missing(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_id.return_value = user
        self.wallet_repository.read_by_column = AsyncMock(return_value=None)
        created_wallet = SimpleNamespace(
            id="wallet-9",
            coinsBalance=0.0,
            pointsBalance=40.0,
            conversionRate=10.0,
            updated_at=datetime(2026, 1, 1, 10, 0, 0),
        )
        self.wallet_repository.create = AsyncMock(return_value=created_wallet)
        self.wallet_repository.update = AsyncMock(return_value=created_wallet)
        self.wallet_transaction_repository.create = MagicMock(
            return_value=SimpleNamespace(id=uuid4())
        )

        response = await self.service.convert_points_to_coins(
            str(user.id), PostPointsConversionRequest(points=20), "api-key"
        )

        self.assertEqual(response.convertedAmount, 2.0)
        self.wallet_repository.create.assert_awaited_once()
        self.wallet_repository.update.assert_awaited_once()

    async def test_convert_points_to_coins_external_user_id_delegates(self):
        user = SimpleNamespace(id=uuid4())
        self.user_repository.read_by_column.return_value = user
        expected = {"transactionId": "tx-1"}
        self.service.convert_points_to_coins = AsyncMock(return_value=expected)

        schema = PostPointsConversionRequest(points=10)
        result = await self.service.convert_points_to_coins_externalUserId(
            "external-user", schema, "api-key"
        )

        self.assertEqual(result, expected)
        self.service.convert_points_to_coins.assert_awaited_once_with(
            str(user.id), schema, "api-key"
        )


if __name__ == "__main__":
    unittest.main()
