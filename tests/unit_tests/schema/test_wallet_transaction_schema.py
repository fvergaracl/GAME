from uuid import uuid4
from app.schema.wallet_transaction_schema import (
    BaseWalletTransactionWithoutWalletId,
    BaseWalletTransaction,
    BaseWalletTransactionInfo
)


def test_base_wallet_transaction_without_wallet_id():
    """
    Test the BaseWalletTransactionWithoutWalletId model.

    The BaseWalletTransactionWithoutWalletId model is used for a wallet
      transaction without wallet ID.

    The model has the following attributes:
    - transactionType (str): Transaction type
    - points (int): Points
    - coins (float): Coins
    - data (Optional[dict]): Additional data
    """
    data = {
        "transactionType": "conversion",
        "points": 100,
        "coins": 50.0,
        "data": {"key": "value"}
    }
    transaction = BaseWalletTransactionWithoutWalletId(**data)
    assert transaction.transactionType == data["transactionType"]
    assert transaction.points == data["points"]
    assert transaction.coins == data["coins"]
    assert transaction.data == data["data"]


def test_base_wallet_transaction():
    """
    Test the BaseWalletTransaction model.

    The BaseWalletTransaction model is used for a wallet transaction.

    The model has the following attributes:
    - walletId (str): Wallet ID
    - appliedConversionRate (float): Applied conversion rate
    """
    data = {
        "transactionType": "conversion",
        "points": 100,
        "coins": 50.0,
        "data": {"key": "value"},
        "walletId": "wallet123",
        "appliedConversionRate": 1.5
    }
    transaction = BaseWalletTransaction(**data)
    assert transaction.transactionType == data["transactionType"]
    assert transaction.points == data["points"]
    assert transaction.coins == data["coins"]
    assert transaction.data == data["data"]
    assert transaction.walletId == data["walletId"]
    assert transaction.appliedConversionRate == data["appliedConversionRate"]


def test_base_wallet_transaction_info():
    """
    Test the BaseWalletTransactionInfo model.

    The BaseWalletTransactionInfo model is used for wallet transaction
      information.

    The model has the following attributes:
    - id (UUID): Unique identifier
    - created_at (str): Created date
    """
    data = {
        "transactionType": "conversion",
        "points": 100,
        "coins": 50.0,
        "data": {"key": "value"},
        "id": uuid4(),
        "created_at": "2023-01-01T00:00:00"
    }
    transaction_info = BaseWalletTransactionInfo(**data)
    assert transaction_info.transactionType == data["transactionType"]
    assert transaction_info.points == data["points"]
    assert transaction_info.coins == data["coins"]
    assert transaction_info.data == data["data"]
    assert transaction_info.id == data["id"]
    assert transaction_info.created_at == data["created_at"]
