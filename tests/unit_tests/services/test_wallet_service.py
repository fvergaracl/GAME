import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.repository.user_repository import UserRepository
from app.repository.wallet_repository import WalletRepository
from app.schema.wallet_schema import BaseWallet, PostPreviewConvertPoints
from app.services.wallet_service import WalletService


class TestWalletService(unittest.TestCase):
    def setUp(self):
        self.wallet_repository = MagicMock(spec=WalletRepository)
        self.user_repository = MagicMock(spec=UserRepository)
        self.service = WalletService(
            wallet_repository=self.wallet_repository,
            user_repository=self.user_repository,
        )

    def test_init_sets_repositories(self):
        self.assertIs(self.service.wallet_repository, self.wallet_repository)
        self.assertIs(self.service.user_repository, self.user_repository)
        self.assertIs(self.service._repository, self.wallet_repository)

    def test_get_wallet_by_user_id_returns_base_wallet(self):
        external_user_id = "external-user-1"
        user = SimpleNamespace(id=1, externalUserId=external_user_id)
        wallet_id = uuid4()
        created_at = datetime(2026, 1, 1, 10, 0, 0)
        updated_at = datetime(2026, 1, 2, 12, 0, 0)
        wallet = SimpleNamespace(
            id=wallet_id,
            coinsBalance=25.5,
            pointsBalance=100.0,
            conversionRate=0.5,
            created_at=created_at,
            updated_at=updated_at,
        )
        self.user_repository.read_by_column.return_value = user
        self.wallet_repository.read_by_column.return_value = wallet

        result = self.service.get_wallet_by_user_id(external_user_id)

        self.assertIsInstance(result, BaseWallet)
        self.assertEqual(result.id, wallet_id)
        self.assertEqual(result.coinsBalance, 25.5)
        self.assertEqual(result.pointsBalance, 100.0)
        self.assertEqual(result.conversionRate, 0.5)
        self.assertEqual(result.created_at, created_at)
        self.assertEqual(result.updated_at, updated_at)
        self.user_repository.read_by_column.assert_called_once_with(
            column="externalUserId",
            value=external_user_id,
            not_found_message=f"User with externalUserId {external_user_id} not found",
        )
        self.wallet_repository.read_by_column.assert_called_once_with(
            column="userId",
            value=user.id,
            not_found_message=f"Wallet with userId {user.id} not found",
        )

    def test_preview_convert_returns_expected_values(self):
        external_user_id = "external-user-2"
        schema = PostPreviewConvertPoints(points=40, externalUserId=external_user_id)
        user = SimpleNamespace(id=2, externalUserId=external_user_id)
        wallet = SimpleNamespace(
            id=uuid4(),
            coinsBalance=10.0,
            pointsBalance=140.0,
            conversionRate=0.25,
            created_at=datetime(2026, 1, 1, 10, 0, 0),
            updated_at=datetime(2026, 1, 2, 12, 0, 0),
        )
        self.user_repository.read_by_column.return_value = user
        self.wallet_repository.read_by_column.return_value = wallet

        result = self.service.preview_convert(schema)

        self.assertEqual(result.coins, 10.0)
        self.assertEqual(result.points_converted, 40.0)
        self.assertEqual(result.conversionRate, 0.25)
        self.assertEqual(result.afterConversionPoints, 100.0)
        self.assertEqual(result.afterConversionCoins, 20.0)
        self.assertEqual(result.externalUserId, external_user_id)
        self.user_repository.read_by_column.assert_called_once_with(
            column="externalUserId",
            value=external_user_id,
            not_found_message=f"User with externalUserId {external_user_id} not found",
        )
        self.wallet_repository.read_by_column.assert_called_once_with(
            column="userId",
            value=user.id,
            not_found_message=f"Wallet with userId {user.id} not found",
        )


if __name__ == "__main__":
    unittest.main()
