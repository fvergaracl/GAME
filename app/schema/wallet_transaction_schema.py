from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class BaseWalletTransactionWithoutWalletId(BaseModel):
    """
    Base model for wallet transaction without wallet ID

    Attributes:
        transactionType (str): Transaction type
        points (int): Points
        coins (float): Coins
        data (Optional[dict]): Additional data
    """
    transactionType: str
    points: int
    coins: float
    data: Optional[dict]


class BaseWalletTransaction(BaseWalletTransactionWithoutWalletId):
    """
    Base model for wallet transaction

    Attributes:
        walletId (str): Wallet ID
        appliedConversionRate (float): Applied conversion rate
    """
    walletId: str
    appliedConversionRate: float


class BaseWalletTransactionInfo(BaseWalletTransactionWithoutWalletId):
    """
    Model for wallet transaction information

    Attributes:
        id (UUID): Unique identifier
        created_at (str): Created date
    """
    id: UUID
    created_at: str
