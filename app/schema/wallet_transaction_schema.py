from pydantic import BaseModel
from typing import Optional
"""
    transactionType: str = Field(sa_column=Column(String))
    points: int = Field(sa_column=Column(Integer))
    appliedConversionRate: float = Field(sa_column=Column(Float))
    walletId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("wallet.id")))

"""


class BaseWalletTransaction(BaseModel):
    transactionType: str
    points: int
    coins: int
    data: Optional[dict]
    appliedConversionRate: float
    walletId: str
