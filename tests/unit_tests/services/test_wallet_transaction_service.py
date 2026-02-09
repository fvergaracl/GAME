import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.repository.wallet_transaction_repository import WalletTransactionRepository
from app.services.wallet_transaction_service import WalletTransactionService


class TestWalletTransactionService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.wallet_transaction_repository = MagicMock(spec=WalletTransactionRepository)
        self.service = WalletTransactionService(self.wallet_transaction_repository)

    def test_init_sets_repositories(self):
        self.assertIs(
            self.service.wallet_transaction_repository, self.wallet_transaction_repository
        )
        self.assertIs(self.service._repository, self.wallet_transaction_repository)

    def test_get_list_delegates_to_repository(self):
        schema = {"page": 1}
        expected = {"items": [], "search_options": {"page": 1}}
        self.wallet_transaction_repository.read_by_options.return_value = expected

        result = self.service.get_list(schema)

        self.wallet_transaction_repository.read_by_options.assert_called_once_with(schema)
        self.assertEqual(result, expected)

    def test_get_by_id_delegates_to_repository(self):
        item_id = uuid4()
        expected = {"id": str(item_id)}
        self.wallet_transaction_repository.read_by_id.return_value = expected

        result = self.service.get_by_id(item_id)

        self.wallet_transaction_repository.read_by_id.assert_called_once_with(item_id)
        self.assertEqual(result, expected)

    async def test_add_delegates_to_repository_create(self):
        schema = {"walletId": "wallet-1", "points": 10}
        expected = {"id": "tx-1"}
        self.wallet_transaction_repository.create = AsyncMock(return_value=expected)

        result = await self.service.add(schema)

        self.wallet_transaction_repository.create.assert_awaited_once_with(schema)
        self.assertEqual(result, expected)

    async def test_patch_delegates_to_repository_update(self):
        item_id = uuid4()
        schema = {"points": 20}
        expected = {"id": str(item_id), "points": 20}
        self.wallet_transaction_repository.update = AsyncMock(return_value=expected)

        result = await self.service.patch(item_id, schema)

        self.wallet_transaction_repository.update.assert_awaited_once_with(item_id, schema)
        self.assertEqual(result, expected)

    def test_patch_attr_delegates_to_repository_update_attr(self):
        item_id = uuid4()
        expected = {"id": str(item_id), "points": 30}
        self.wallet_transaction_repository.update_attr.return_value = expected

        result = self.service.patch_attr(item_id, "points", 30)

        self.wallet_transaction_repository.update_attr.assert_called_once_with(
            item_id, "points", 30
        )
        self.assertEqual(result, expected)

    def test_put_update_delegates_to_repository_whole_update(self):
        item_id = uuid4()
        schema = {"transactionType": "AssignPoints", "points": 40}
        expected = {"id": str(item_id), "transactionType": "AssignPoints", "points": 40}
        self.wallet_transaction_repository.whole_update.return_value = expected

        result = self.service.put_update(item_id, schema)

        self.wallet_transaction_repository.whole_update.assert_called_once_with(
            item_id, schema
        )
        self.assertEqual(result, expected)

    def test_remove_by_id_delegates_to_repository_delete_by_id(self):
        item_id = uuid4()
        self.wallet_transaction_repository.delete_by_id.return_value = None

        result = self.service.remove_by_id(item_id)

        self.wallet_transaction_repository.delete_by_id.assert_called_once_with(item_id)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
