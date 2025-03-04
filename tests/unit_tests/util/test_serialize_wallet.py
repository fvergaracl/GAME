import unittest
from datetime import datetime
from uuid import uuid4

from app.util.serialize_wallet import serialize_wallet

# Modelo Wallet de ejemplo


class Wallet:
    def __init__(self, id, name, created_at, balance, _internal_value=None):
        self.id = id
        self.name = name
        self.created_at = created_at
        self.balance = balance
        self._internal_value = _internal_value


class TestSerializeWallet(unittest.TestCase):

    def test_serialize_uuid(self):
        """
        Test that a UUID field is correctly serialized to a string.
        """
        wallet = Wallet(
            id=uuid4(), name="My Wallet", created_at=datetime.now(), balance=100.0
        )
        serialized = serialize_wallet(wallet)
        self.assertIsInstance(serialized["id"], str)
        self.assertEqual(serialized["id"], str(wallet.id))

    def test_serialize_datetime(self):
        """
        Test that a datetime field is correctly serialized to ISO 8601 format.
        """
        now = datetime.now()
        wallet = Wallet(id=uuid4(), name="My Wallet", created_at=now, balance=100.0)
        serialized = serialize_wallet(wallet)
        self.assertIsInstance(serialized["created_at"], str)
        self.assertEqual(serialized["created_at"], now.isoformat())

    def test_serialize_other_fields(self):
        """
        Test that non-UUID and non-datetime fields are serialized correctly.
        """
        wallet = Wallet(
            id=uuid4(), name="My Wallet", created_at=datetime.now(), balance=100.0
        )
        serialized = serialize_wallet(wallet)
        self.assertEqual(serialized["name"], wallet.name)
        self.assertEqual(serialized["balance"], wallet.balance)

    def test_internal_fields_are_ignored(self):
        """
        Test that internal fields (starting with "_") are not serialized.
        """
        wallet = Wallet(
            id=uuid4(),
            name="My Wallet",
            created_at=datetime.now(),
            balance=100.0,
            _internal_value="should be ignored",
        )
        serialized = serialize_wallet(wallet)
        self.assertNotIn("_internal_value", serialized)

    def test_empty_wallet(self):
        """
        Test that serializing an empty wallet object still works.
        """
        wallet = Wallet(id=uuid4(), name=None, created_at=None, balance=None)
        serialized = serialize_wallet(wallet)
        self.assertIsNone(serialized["name"])
        self.assertIsNone(serialized["created_at"])
        self.assertIsNone(serialized["balance"])


if __name__ == "__main__":
    unittest.main()
