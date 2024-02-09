import pytest
from datetime import datetime, timezone
from app.model.wallet_transactions import WalletTransactions
from uuid import uuid4


def test_wallet_transactions_creation_and_representation():
    now = datetime.now(timezone.utc)
    wallet_id = str(uuid4())
    transaction = WalletTransactions(
        created_at=now,
        updated_at=now,
        transactionType="DepositCoins",
        points=100,
        coins=50.0,
        data={"description": "Deposit into wallet"},
        appliedConversionRate=1.0,
        walletId=wallet_id
    )

    expected_str = (
        f"WalletTransactions: (id={transaction.id}, created_at={now}, updated_at={now}, "
        f"transactionType=DepositCoins, points=100, coins=50.0, "
        f"data={{'description': 'Deposit into wallet'}}, appliedConversionRate=1.0, walletId={wallet_id})"
    )
    assert str(transaction) == expected_str
    assert repr(transaction) == expected_str


def test_wallet_transactions_equality():
    wallet_id = str(uuid4())
    transaction1 = WalletTransactions(
        transactionType="EarnRewards",
        points=500,
        coins=0.0,
        data={"event": "Completed task"},
        appliedConversionRate=0.0,
        walletId=wallet_id
    )
    transaction2 = WalletTransactions(
        transactionType="EarnRewards",
        points=500,
        coins=0.0,
        data={"event": "Completed task"},
        appliedConversionRate=0.0,
        walletId=wallet_id
    )

    # Even if all attributes match, transactions are unique by their id
    assert transaction1 != transaction2

    # Testing with the same ID for both instances
    transaction2.id = transaction1.id
    assert transaction1 == transaction2


def test_wallet_transactions_hash():
    wallet_id = str(uuid4())
    transaction = WalletTransactions(
        transactionType="WithdrawCoins",
        points=0,
        coins=20.0,
        data={"description": "Withdrawal from wallet"},
        appliedConversionRate=1.0,
        walletId=wallet_id
    )

    # Use the make_hashable method to prepare the 'data' field for hashing
    data_as_hashable = transaction.make_hashable(transaction.data)

    # Now 'data_as_hashable' is used in the hash comparison
    assert hash(transaction) == hash(
        (
            transaction.transactionType,
            transaction.points,
            transaction.coins,
            data_as_hashable,  # Use the hashable version of 'data'
            transaction.appliedConversionRate,
            transaction.walletId,
        )
    )
