from datetime import datetime
from uuid import uuid4

from app.model.wallet_transactions import WalletTransactions


def create_wallet_transaction_instance():
    return WalletTransactions(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        transactionType="AssignPoints",
        points=100,
        coins=10.5,
        data={"description": "Test transaction"},
        appliedConversionRate=1.5,
        walletId=str(uuid4()),
    )


def test_wallet_transaction_creation():
    """
    Test the creation of a WalletTransactions instance.
    """
    transaction = create_wallet_transaction_instance()
    assert isinstance(transaction, WalletTransactions)
    assert isinstance(transaction.id, str)
    assert isinstance(transaction.created_at, datetime)
    assert isinstance(transaction.updated_at, datetime)
    assert transaction.transactionType == "AssignPoints"
    assert transaction.points == 100
    assert transaction.coins == 10.5
    assert transaction.data == {"description": "Test transaction"}
    assert transaction.appliedConversionRate == 1.5
    assert isinstance(transaction.walletId, str)


def test_wallet_transaction_str():
    """
    Test the __str__ method of WalletTransactions.
    """
    transaction = create_wallet_transaction_instance()
    expected_str = (
        f"WalletTransactions: (id={transaction.id}, "
        f"created_at={transaction.created_at},"
        f" updated_at={transaction.updated_at}, "
        f"transactionType={transaction.transactionType}, "
        f"points={transaction.points}, "
        f"coins={transaction.coins}, data={transaction.data}, "
        f"appliedConversionRate={transaction.appliedConversionRate}, "
        f"walletId={transaction.walletId})"
    )
    assert str(transaction) == expected_str


def test_wallet_transaction_repr():
    """
    Test the __repr__ method of WalletTransactions.
    """
    transaction = create_wallet_transaction_instance()
    expected_repr = (
        f"WalletTransactions: (id={transaction.id}, "
        f"created_at={transaction.created_at}, "
        f"updated_at={transaction.updated_at}, "
        f"transactionType={transaction.transactionType}, "
        f"points={transaction.points}, "
        f"coins={transaction.coins}, data={transaction.data}, "
        f"appliedConversionRate={transaction.appliedConversionRate}, "
        f"walletId={transaction.walletId})"
    )
    assert repr(transaction) == expected_repr


def test_wallet_transaction_equality():
    """
    Test the equality operator for WalletTransactions.
    """
    transaction1 = create_wallet_transaction_instance()
    transaction2 = create_wallet_transaction_instance()
    assert transaction1 != transaction2
    transaction2.id = transaction1.id
    transaction2.transactionType = transaction1.transactionType
    transaction2.points = transaction1.points
    transaction2.coins = transaction1.coins
    transaction2.data = transaction1.data
    transaction2.appliedConversionRate = transaction1.appliedConversionRate
    transaction2.walletId = transaction1.walletId
    assert transaction1 == transaction2


def test_wallet_transaction_hash():
    """
    Test the __hash__ method of WalletTransactions.
    """
    transaction = create_wallet_transaction_instance()
    data_as_hashable = (
        tuple(sorted((k, v) for k, v in transaction.data.items()))
        if transaction.data
        else None
    )
    expected_hash = hash(
        (
            transaction.transactionType,
            transaction.points,
            transaction.coins,
            data_as_hashable,
            transaction.appliedConversionRate,
            transaction.walletId,
        )
    )
    assert hash(transaction) == expected_hash


def test_wallet_transaction_make_hashable_with_nested_list_structure():
    """
    Ensure nested lists/tuples are converted to hashable tuples recursively.
    """
    transaction = create_wallet_transaction_instance()

    raw_data = [{"k": [1, 2]}, ("a", "b")]
    converted = transaction.make_hashable(raw_data)

    assert isinstance(converted, tuple)
    assert converted[0][0][0] == "k"
    assert converted[0][0][1] == (1, 2)
    assert converted[1] == ("a", "b")
