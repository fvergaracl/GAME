from app.model.base_model import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer, Float, String
from sqlalchemy.dialects.postgresql import UUID


class WalletTransactions(BaseModel, table=True):
    transactionType: str = Field(sa_column=Column(String))
    points: int = Field(sa_column=Column(Integer))
    appliedConversionRate: float = Field(sa_column=Column(Float))
    walletId: int = Field(sa_column=Column(
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
