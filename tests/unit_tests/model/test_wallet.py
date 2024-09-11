from datetime import datetime
from uuid import uuid4

from app.core.config import configs
from app.model.wallet import Wallet


def create_wallet_instance():
    return Wallet(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        coinsBalance=100.0,
        pointsBalance=200.0,
        conversionRate=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN,
        userId=str(uuid4()),
    )


def test_wallet_creation():
    """
    Test the creation of a Wallet instance.
    """
    wallet = create_wallet_instance()
    assert isinstance(wallet, Wallet)
    assert isinstance(wallet.id, str)
    assert isinstance(wallet.created_at, datetime)
    assert isinstance(wallet.updated_at, datetime)
    assert wallet.coinsBalance == 100.0
    assert wallet.pointsBalance == 200.0
    assert wallet.conversionRate == (configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN)
    assert isinstance(wallet.userId, str)


def test_wallet_str():
    """
    Test the __str__ method of Wallet.
    """
    wallet = create_wallet_instance()
    expected_str = (
        f"Wallet: (id={wallet.id}, created_at={wallet.created_at}, "
        f"updated_at={wallet.updated_at}, coinsBalance={wallet.coinsBalance}, "
        f"pointsBalance={wallet.pointsBalance}, "
        f"conversionRate={wallet.conversionRate}, userId={wallet.userId} )"
    )
    assert str(wallet) == expected_str


def test_wallet_repr():
    """
    Test the __repr__ method of Wallet.
    """
    wallet = create_wallet_instance()
    expected_repr = (
        f"Wallet: (id={wallet.id}, created_at={wallet.created_at}, "
        f"updated_at={wallet.updated_at}, coinsBalance={wallet.coinsBalance}, "
        f"pointsBalance={wallet.pointsBalance}, "
        f"conversionRate={wallet.conversionRate}, userId={wallet.userId} )"
    )
    assert repr(wallet) == expected_repr


def test_wallet_equality():
    """
    Test the equality operator for Wallet.
    """
    wallet1 = create_wallet_instance()
    wallet2 = create_wallet_instance()
    assert wallet1 != wallet2  # Different instances should not be equal
    wallet2.id = wallet1.id
    wallet2.coinsBalance = wallet1.coinsBalance
    wallet2.pointsBalance = wallet1.pointsBalance
    wallet2.conversionRate = wallet1.conversionRate
    wallet2.userId = wallet1.userId
    assert wallet1 == wallet2  # Same attributes should be equal


def test_wallet_hash():
    """
    Test the __hash__ method of Wallet.
    """
    wallet = create_wallet_instance()
    expected_hash = hash(
        (
            wallet.id,
            wallet.coinsBalance,
            wallet.pointsBalance,
            wallet.conversionRate,
            wallet.userId,
        )
    )
    assert hash(wallet) == expected_hash
