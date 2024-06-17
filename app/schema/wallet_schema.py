from typing import Optional

from pydantic import BaseModel

from app.schema.base_schema import ModelBaseInfo


class WalletWithoutUserId(BaseModel):
    """
    Model for wallet without user ID

    Attributes:
        coinsBalance (Optional[float]): Coins balance
        pointsBalance (Optional[float]): Points balance
        conversionRate (Optional[float]): Conversion rate
    """

    coinsBalance: Optional[float]
    pointsBalance: Optional[float]
    conversionRate: Optional[float]


class Wallet(WalletWithoutUserId):
    """
    Model for wallet

    Attributes:
        userId (Optional[str]): User ID
    """

    userId: Optional[str]


class BaseWallet(ModelBaseInfo):
    """
    Base model for wallet

    Attributes:
        coinsBalance (Optional[float]): Coins balance
        pointsBalance (Optional[float]): Points balance
        conversionRate (Optional[float]): Conversion rate
        userId (Optional[int]): User ID
    """

    coinsBalance: Optional[float]
    pointsBalance: Optional[float]
    conversionRate: Optional[float]
    userId: Optional[int]


class BaseWalletOnlyUserId(BaseModel):
    """
    Model for wallet with only user ID

    Attributes:
        userId (int): User ID
        pointsBalance (Optional[float]): Points balance
    """

    userId: int
    pointsBalance: Optional[float]


class PostPreviewConvertPoints(BaseModel):
    """
    Model for previewing points conversion

    Attributes:
        points (float): Points
        externalUserId (str): External user ID
    """

    points: float
    externalUserId: str


class ResponsePreviewConvertPoints(BaseModel):
    """
    Model for points conversion preview response

    Attributes:
        coins (float): Coins
        points_converted (float): Points converted
        conversionRate (float): Conversion rate
        afterConversionPoints (float): Points after conversion
        afterConversionCoins (float): Coins after conversion
        externalUserId (str): External user ID
    """

    coins: float
    points_converted: float
    conversionRate: float
    afterConversionPoints: float
    afterConversionCoins: float
    externalUserId: str


class CreateWallet(Wallet):
    """Model for creating a wallet."""

    ...
