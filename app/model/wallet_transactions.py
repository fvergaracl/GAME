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
  "AdjustBalance": "Manual adjustment of the balance (for errors or corrections).",
  "TransferPoints": "Transfer of points to another user.",
  "TransferCoins": "Transfer of coins to another user.",
  "ExchangeCoins": "Exchange of coins for another type of currency or asset.",
  "FeeDeduction": "Deduction of fees or commissions from the balance.",
  "BonusPointsAward": "Awarding of bonus points."
}

"""

from app.model.base_model import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer, Float, String
from sqlalchemy.dialects.postgresql import UUID, JSONB


class WalletTransactions(BaseModel, table=True):
    transactionType: str = Field(sa_column=Column(String))
    points: int = Field(sa_column=Column(Integer))
    coins: int = Field(sa_column=Column(Integer))
    data: dict = Field(sa_column=Column(JSONB), nullable=True)
    appliedConversionRate: float = Field(sa_column=Column(Float))
    walletId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("wallet.id")))

    def __str__(self):
        return f"WalletTransactions: {self.transactionType}, {self.points}, {self.appliedConversionRate}, {self.walletId}"

    def __repr__(self):
        return f"WalletTransactions: {self.transactionType}, {self.points}, {self.appliedConversionRate}, {self.walletId}"

    def __eq__(self, other):
        return self.transactionType == other.transactionType and self.points == other.points and self.appliedConversionRate == other.appliedConversionRate and self.walletId == other.walletId

    def __hash__(self):
        return hash((self.transactionType, self.points, self.appliedConversionRate, self.walletId))

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.walletId < other.walletId
