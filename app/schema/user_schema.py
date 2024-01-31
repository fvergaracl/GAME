from pydantic import BaseModel
from app.schema.base_schema import ModelBaseInfo
from app.schema.wallet_schema import WalletWithoutUserId, Wallet
from app.schema.wallet_transaction_schema import BaseWalletTransactionInfo
from uuid import UUID
from typing import Optional


class BaseUser(BaseModel):
    externalUserId: str


class PostCreateUser(BaseUser):
    ...


class CreatedUser(ModelBaseInfo, BaseUser):
    ...


class PostAssignPointsToUser(BaseModel):
    taskId: UUID
    points: int
    # allow json into description
    data: Optional[dict]


class CreateWallet(Wallet):
    ...


class UserWallet(BaseModel):
    userId: str
    wallet: Optional[WalletWithoutUserId]
    walletTransactions: Optional[list[BaseWalletTransactionInfo]]
