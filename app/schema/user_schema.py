from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.schema.base_schema import ModelBaseInfo
from app.schema.task_schema import TaskPointsResponseByUser
from app.schema.wallet_schema import Wallet, WalletWithoutUserId
from app.schema.wallet_transaction_schema import BaseWalletTransactionInfo


class BaseUser(BaseModel):
    externalUserId: str


class PostCreateUser(BaseUser):
    ...


class UserBasicInfo(ModelBaseInfo, BaseUser):
    ...


class CreatedUser(ModelBaseInfo, BaseUser):
    ...


class PostAssignPointsToUser(BaseModel):
    taskId: UUID
    points: Optional[int]
    description: Optional[str]
    data: Optional[dict]


class CreateWallet(Wallet):
    ...


class UserWallet(BaseModel):
    userId: str
    wallet: Optional[WalletWithoutUserId]
    walletTransactions: Optional[list[BaseWalletTransactionInfo]]


class UserPointsTasks(BaseModel):
    id: UUID
    tasks: list[TaskPointsResponseByUser]


class ResponseConversionPreview(BaseModel):
    points: int
    conversionRate: float
    conversionRateDate: str
    convertedAmount: float
    convertedCurrency: str
    haveEnoughPoints: bool


class PostPointsConversionRequest(BaseModel):
    points: int


class ResponsePointsConversion(BaseModel):
    transactionId: str
    points: int
    conversionRate: float
    conversionRateDate: str
    convertedAmount: float
    convertedCurrency: str
    haveEnoughPoints: bool
