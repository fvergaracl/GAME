from datetime import datetime
from uuid import uuid4

from app.schema.wallet_schema import (BaseWallet, BaseWalletOnlyUserId, CreateWallet,
                                      PostPreviewConvertPoints,
                                      ResponsePreviewConvertPoints, Wallet,
                                      WalletWithoutUserId)


def test_wallet_without_user_id():
    """
    Test the WalletWithoutUserId model.

    The WalletWithoutUserId model is used for a wallet without a user ID.

    The model has the following attributes:
    - coinsBalance (Optional[float]): Coins balance
    - pointsBalance (Optional[float]): Points balance
    - conversionRate (Optional[float]): Conversion rate
    """
    data = {"coinsBalance": 100.0, "pointsBalance": 200.0, "conversionRate": 1.5}
    wallet = WalletWithoutUserId(**data)
    assert wallet.coinsBalance == data["coinsBalance"]
    assert wallet.pointsBalance == data["pointsBalance"]
    assert wallet.conversionRate == data["conversionRate"]


def test_wallet():
    """
    Test the Wallet model.

    The Wallet model is used for a wallet with a user ID.

    The model has the following attributes:
    - coinsBalance (Optional[float]): Coins balance
    - pointsBalance (Optional[float]): Points balance
    - conversionRate (Optional[float]): Conversion rate
    - userId (Optional[str]): User ID
    """
    data = {
        "coinsBalance": 100.0,
        "pointsBalance": 200.0,
        "conversionRate": 1.5,
        "userId": "user123",
    }
    wallet = Wallet(**data)
    assert wallet.coinsBalance == data["coinsBalance"]
    assert wallet.pointsBalance == data["pointsBalance"]
    assert wallet.conversionRate == data["conversionRate"]
    assert wallet.userId == data["userId"]


def test_base_wallet():
    """
    Test the BaseWallet model.

    The BaseWallet model is used as a base model for a wallet.

    The model has the following attributes:
    - coinsBalance (Optional[float]): Coins balance
    - pointsBalance (Optional[float]): Points balance
    - conversionRate (Optional[float]): Conversion rate
    - userId (Optional[int]): User ID
    """
    data = {
        "id": uuid4(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "coinsBalance": 100.0,
        "pointsBalance": 200.0,
        "conversionRate": 1.5,
        "userId": 123,
    }
    wallet = BaseWallet(**data)
    assert wallet.id == data["id"]
    assert wallet.created_at == data["created_at"]
    assert wallet.updated_at == data["updated_at"]
    assert wallet.coinsBalance == data["coinsBalance"]
    assert wallet.pointsBalance == data["pointsBalance"]
    assert wallet.conversionRate == data["conversionRate"]
    assert wallet.userId == data["userId"]


def test_base_wallet_only_user_id():
    """
    Test the BaseWalletOnlyUserId model.

    The BaseWalletOnlyUserId model is used for a wallet with only a user ID.

    The model has the following attributes:
    - userId (int): User ID
    - pointsBalance (Optional[float]): Points balance
    """
    data = {"userId": 123, "pointsBalance": 200.0}
    wallet = BaseWalletOnlyUserId(**data)
    assert wallet.userId == data["userId"]
    assert wallet.pointsBalance == data["pointsBalance"]


def test_post_preview_convert_points():
    """
    Test the PostPreviewConvertPoints model.

    The PostPreviewConvertPoints model is used for previewing points
      conversion.

    The model has the following attributes:
    - points (float): Points
    - externalUserId (str): External user ID
    """
    data = {"points": 100.0, "externalUserId": "user123"}
    preview = PostPreviewConvertPoints(**data)
    assert preview.points == data["points"]
    assert preview.externalUserId == data["externalUserId"]


def test_response_preview_convert_points():
    """
    Test the ResponsePreviewConvertPoints model.

    The ResponsePreviewConvertPoints model is used for points conversion
      preview response.

    The model has the following attributes:
    - coins (float): Coins
    - points_converted (float): Points converted
    - conversionRate (float): Conversion rate
    - afterConversionPoints (float): Points after conversion
    - afterConversionCoins (float): Coins after conversion
    - externalUserId (str): External user ID
    """
    data = {
        "coins": 50.0,
        "points_converted": 100.0,
        "conversionRate": 1.5,
        "afterConversionPoints": 200.0,
        "afterConversionCoins": 75.0,
        "externalUserId": "user123",
    }
    response = ResponsePreviewConvertPoints(**data)
    assert response.coins == data["coins"]
    assert response.points_converted == data["points_converted"]
    assert response.conversionRate == data["conversionRate"]
    assert response.afterConversionPoints == data["afterConversionPoints"]
    assert response.afterConversionCoins == data["afterConversionCoins"]
    assert response.externalUserId == data["externalUserId"]


def test_create_wallet():
    """
    Test the CreateWallet model.

    The CreateWallet model is used for creating a wallet.
    """
    data = {
        "coinsBalance": 100.0,
        "pointsBalance": 200.0,
        "conversionRate": 1.5,
        "userId": "user123",
    }
    wallet = CreateWallet(**data)
    assert wallet.coinsBalance == data["coinsBalance"]
    assert wallet.pointsBalance == data["pointsBalance"]
    assert wallet.conversionRate == data["conversionRate"]
    assert wallet.userId == data["userId"]
