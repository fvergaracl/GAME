import pytest
from datetime import datetime, timezone
from app.model.wallet import Wallet
from uuid import uuid4
from app.core.config import configs


def test_wallet_initialization():
    user_id = str(uuid4())
    wallet = Wallet(
        userId=user_id
    )

    # Check default values
    assert wallet.coinsBalance == 0.0
    assert wallet.pointsBalance == 0.0
    assert wallet.conversionRate == configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN
    assert wallet.userId == user_id


def test_wallet_string_representation():
    now = datetime.now(timezone.utc)
    user_id = str(uuid4())
    wallet = Wallet(
        created_at=now,
        updated_at=now,
        userId=user_id
    )

    expected_str = (
        f"Wallet: (id={wallet.id}, created_at={wallet.created_at}, "
        f"updated_at={wallet.updated_at}, coinsBalance={wallet.coinsBalance}, "
        f"pointsBalance={wallet.pointsBalance}, "
        f"conversionRate={wallet.conversionRate}, userId={wallet.userId} )"
    )
    assert str(wallet) == expected_str
    assert repr(wallet) == expected_str


def test_wallet_equality():
    user_id = str(uuid4())
    wallet1 = Wallet(userId=user_id)
    wallet2 = Wallet(userId=user_id)

    # Wallets are unique by their id, even if all other attributes match
    assert wallet1 != wallet2

    # Force the same id for testing equality
    wallet2.id = wallet1.id
    assert wallet1 == wallet2


def test_wallet_hash():
    user_id = str(uuid4())
    wallet = Wallet(userId=user_id)

    # Ensure hash incorporates all relevant fields
    assert hash(wallet) == hash(
        (wallet.id, wallet.coinsBalance, wallet.pointsBalance,
         wallet.conversionRate, wallet.userId)
    )
