"""
transactions Types:
{
  "AssignPoints": "Assignment of points to the wallet.",
  "ConvertPointsToCoins": "Conversion of points to coins in the wallet.",
  "DepositCoins": "Deposit of coins into the wallet.",
  "WithdrawCoins": "Withdrawal of coins from the wallet.",
  "EarnRewards": "Earning rewards (points or coins) for specific activities.",
  "RedeemRewards": "Redemption of points for rewards or services.",
  "PurchaseWithPoints": "Purchase of items or services using points.",
  "PurchaseWithCoins": "Purchase of items or services using coins.",
  "RefundTransaction": "Refund of a previous transaction.",
  "AdjustBalance": "Manual adjustment of the balance (for errors or
  corrections).",
  "TransferPoints": "Transfer of points to another user.",
  "TransferCoins": "Transfer of coins to another user.",
  "ExchangeCoins": "Exchange of coins for another type of currency or asset.",
  "FeeDeduction": "Deduction of fees or commissions from the balance.",
  "BonusPointsAward": "Awarding of bonus points."
}

"""

from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlmodel import Column, Field, Float, ForeignKey, Integer, String

from app.model.base_model import BaseModel


class WalletTransactions(BaseModel, table=True):
    """
    Represents a transaction in a wallet.

    Attributes:
        transactionType (str): The type of transaction.
        points (int): The number of points involved in the transaction.
        coins (float): The number of coins involved in the transaction.
        data (dict): Additional data associated with the transaction.
        appliedConversionRate (float): The conversion rate applied to the transaction.
        walletId (str): The ID of the wallet associated with the transaction.
    """

    transactionType: str = Field(sa_column=Column(String))
    points: int = Field(sa_column=Column(Integer))
    coins: float = Field(sa_column=Column(Float))
    data: dict = Field(sa_column=Column(JSONB), nullable=True)
    appliedConversionRate: float = Field(sa_column=Column(Float))
    walletId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("wallet.id")))

    class Config:  # noqa
        orm_mode = True  # noqa

    def __str__(self):
        return f"WalletTransactions: (id={self.id}, created_at={self.created_at}, updated_at={self.updated_at}, transactionType={self.transactionType}, points={self.points}, coins={self.coins}, data={self.data}, appliedConversionRate={self.appliedConversionRate}, walletId={self.walletId})"

    def __repr__(self):
        return f"WalletTransactions: (id={self.id}, created_at={self.created_at}, updated_at={self.updated_at}, transactionType={self.transactionType}, points={self.points}, coins={self.coins}, data={self.data}, appliedConversionRate={self.appliedConversionRate}, walletId={self.walletId})"

    def __eq__(self, other):
        return (
            isinstance(other, WalletTransactions)
            and self.id == other.id
            and self.transactionType == other.transactionType
            and self.points == other.points
            and self.coins == other.coins
            and self.data == other.data
            and self.appliedConversionRate == other.appliedConversionRate
            and self.walletId == other.walletId
        )

    def make_hashable(self, obj):
        if isinstance(obj, (tuple, list)):
            return tuple(self.make_hashable(e) for e in obj)
        elif isinstance(obj, dict):
            return tuple(sorted((k, self.make_hashable(v)) for k, v in obj.items()))
        else:
            return obj

    def __hash__(self):
        data_as_hashable = self.make_hashable(self.data)
        return hash((self.transactionType, self.points, self.coins, data_as_hashable, self.appliedConversionRate, self.walletId))
