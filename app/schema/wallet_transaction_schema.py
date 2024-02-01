from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class BaseWalletTransactionWithoutWalletId(BaseModel):
    transactionType: str
    points: int
    coins: float
    data: Optional[dict]


class BaseWalletTransaction(BaseWalletTransactionWithoutWalletId):
    walletId: str
    appliedConversionRate: float


class BaseWalletTransactionInfo(BaseWalletTransactionWithoutWalletId):
    id: UUID
