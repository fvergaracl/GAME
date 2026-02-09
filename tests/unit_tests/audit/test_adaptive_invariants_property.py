import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.schema.user_schema import PostPointsConversionRequest
from app.services.user_service import UserService
from tests.helpers.property_imports import given, settings, st


class _DummyRepository:
    pass


class InMemoryUserRepository:
    def __init__(self, user_id: str = "user-1", external_user_id: str = "external-user-1"):
        self.user = SimpleNamespace(id=user_id, externalUserId=external_user_id)

    def read_by_id(self, user_id, **_kwargs):
        assert str(user_id) == str(self.user.id)
        return self.user

    def read_by_column(self, column, value, **_kwargs):
        if column == "externalUserId" and value == self.user.externalUserId:
            return self.user
        return None


class InMemoryWalletRepository:
    def __init__(self, user_id: str, points_balance: int, coins_balance: float, conversion_rate: int):
        self.wallet = SimpleNamespace(
            id=str(uuid4()),
            userId=user_id,
            pointsBalance=points_balance,
            coinsBalance=coins_balance,
            conversionRate=conversion_rate,
            updated_at=datetime.now(timezone.utc),
        )
        self.update_calls = 0

    async def read_by_column(self, column, value, **_kwargs):
        if column == "userId" and str(value) == str(self.wallet.userId):
            return self.wallet
        return None

    async def create(self, schema):
        self.wallet = SimpleNamespace(
            id=str(uuid4()),
            userId=str(schema.userId),
            pointsBalance=schema.pointsBalance,
            coinsBalance=schema.coinsBalance,
            conversionRate=schema.conversionRate,
            updated_at=datetime.now(timezone.utc),
        )
        return self.wallet

    async def update(self, wallet_id, wallet):
        assert str(wallet_id) == str(self.wallet.id)
        self.wallet = wallet
        self.wallet.updated_at = datetime.now(timezone.utc)
        self.update_calls += 1
        return self.wallet


class InMemoryWalletTransactionRepository:
    def __init__(self):
        self.transactions = []

    def create(self, schema):
        transaction = SimpleNamespace(id=str(uuid4()), **schema.dict())
        self.transactions.append(transaction)
        return transaction


def _build_user_service(initial_points: int, conversion_rate: int, initial_coins: float = 0.0):
    user_repo = InMemoryUserRepository()
    wallet_repo = InMemoryWalletRepository(
        user_id=user_repo.user.id,
        points_balance=initial_points,
        coins_balance=initial_coins,
        conversion_rate=conversion_rate,
    )
    wallet_tx_repo = InMemoryWalletTransactionRepository()
    service = UserService(
        user_repository=user_repo,
        user_points_repository=_DummyRepository(),
        task_repository=_DummyRepository(),
        wallet_repository=wallet_repo,
        wallet_transaction_repository=wallet_tx_repo,
    )
    return service, wallet_repo, wallet_tx_repo


@settings(max_examples=35)
@given(
    initial_points=st.integers(min_value=1, max_value=5000),
    conversion_rate=st.integers(min_value=1, max_value=500),
    request_points_raw=st.integers(min_value=1, max_value=5000),
)
def test_property_wallet_conversion_preserves_value_and_non_negative_balances(
    initial_points,
    conversion_rate,
    request_points_raw,
):
    request_points = (request_points_raw % initial_points) + 1
    service, wallet_repo, wallet_tx_repo = _build_user_service(
        initial_points=initial_points,
        conversion_rate=conversion_rate,
    )

    before_points = wallet_repo.wallet.pointsBalance
    before_coins = wallet_repo.wallet.coinsBalance
    before_equivalent_points = before_points + (before_coins * conversion_rate)

    response = asyncio.run(
        service.convert_points_to_coins(
            userId="user-1",
            schema=PostPointsConversionRequest(points=request_points),
            api_key="api-key-1",
        )
    )

    after_points = wallet_repo.wallet.pointsBalance
    after_coins = wallet_repo.wallet.coinsBalance
    after_equivalent_points = after_points + (after_coins * conversion_rate)

    assert response.points == request_points
    assert after_points == before_points - request_points
    assert after_points >= 0
    assert after_coins == pytest.approx(before_coins + (request_points / conversion_rate))
    assert after_equivalent_points == pytest.approx(before_equivalent_points)
    assert len(wallet_tx_repo.transactions) == 1


@settings(max_examples=25)
@given(
    initial_points=st.integers(min_value=1, max_value=3000),
    conversion_rate=st.integers(min_value=1, max_value=300),
)
def test_property_full_conversion_is_not_double_spend(initial_points, conversion_rate):
    service, wallet_repo, wallet_tx_repo = _build_user_service(
        initial_points=initial_points,
        conversion_rate=conversion_rate,
    )
    schema = PostPointsConversionRequest(points=initial_points)

    first = asyncio.run(
        service.convert_points_to_coins(
            userId="user-1",
            schema=schema,
            api_key="api-key-1",
        )
    )
    points_after_first = wallet_repo.wallet.pointsBalance
    coins_after_first = wallet_repo.wallet.coinsBalance

    with pytest.raises(ValueError, match="Not enough points"):
        asyncio.run(
            service.convert_points_to_coins(
                userId="user-1",
                schema=schema,
                api_key="api-key-1",
            )
        )

    assert first.points == initial_points
    assert points_after_first == 0
    assert wallet_repo.wallet.pointsBalance == points_after_first
    assert wallet_repo.wallet.coinsBalance == coins_after_first
    assert len(wallet_tx_repo.transactions) == 1


@settings(max_examples=30)
@given(
    points=st.integers(min_value=1, max_value=50),
    minutes=st.integers(min_value=0, max_value=120),
)
def test_property_greengage_time_effects_are_bounded(points, minutes):
    with patch(
        "app.engine.greengageStrategy.Container.task_service",
        new=MagicMock(return_value=MagicMock()),
    ), patch(
        "app.engine.greengageStrategy.Container.user_points_service",
        new=MagicMock(return_value=MagicMock()),
    ):
        from app.engine.greengageStrategy import GREENGAGEGamificationStrategy

        strategy = GREENGAGEGamificationStrategy()

    dpte = strategy.get_DPTE(points=points, minutes=minutes)
    bp = strategy.get_BP(points=points, minutes=minutes)
    pbp = strategy.get_PBP(points=points, minutes=minutes)

    assert 0 <= dpte <= points * 60
    assert bp >= dpte
    assert pbp >= dpte
    assert bp >= pbp
