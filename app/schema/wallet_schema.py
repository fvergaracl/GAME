from pydantic import BaseModel
from typing import Optional
from app.schema.base_schema import ModelBaseInfo


class WalletWithoutUserId(BaseModel):
    coinsBalance: Optional[float]
    pointsBalance: Optional[float]
    conversionRate: Optional[float]

class Wallet(WalletWithoutUserId):
    userId: Optional[str]


class BaseWallet(ModelBaseInfo):
    coinsBalance: Optional[float]
    pointsBalance: Optional[float]
    conversionRate: Optional[float]
    userId: Optional[int]


class BaseWalletOnlyUserId(BaseModel):
    userId: int
    pointsBalance: Optional[float]


class PostPreviewConvertPoints(BaseModel):
    points: float
    externalUserId: str


class ResponsePreviewConvertPoints(BaseModel):
    coins: float
    points_converted: float
    conversionRate: float
    afterConversionPoints: float
    afterConversionCoins: float
    externalUserId: str
