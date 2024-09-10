from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, Field, Float, ForeignKey, Integer, String

from app.core.config import configs
from app.model.base_model import BaseModel


class Wallet(BaseModel, table=True):
    """
    Represents a user's wallet.

    Attributes:
        coinsBalance (float): The balance of coins in the wallet.
        pointsBalance (float): The balance of points in the wallet.
        conversionRate (float): The conversion rate from points to coins.
        userId (str): The ID of the user associated with the wallet.
    """

    coinsBalance: float = Field(sa_column=Column(Float), default=0.0)
    pointsBalance: float = Field(sa_column=Column(Float), default=0.0)
    conversionRate: float = Field(
        sa_column=Column(Integer),
        default=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN,
    )
    userId: str = Field(
        sa_column=Column(
            UUID(as_uuid=True), ForeignKey("users.id"), unique=True,
            nullable=False
        )
    )
    apiKey_used: str = Field(
        sa_column=Column(String, ForeignKey(
            "apikey.apiKey"), nullable=True)
    )

    class Config:  # noqa
        orm_mode = True  # noqa

    def __str__(self):
        return (
            f"Wallet: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, coinsBalance={self.coinsBalance}, "
            f"pointsBalance={self.pointsBalance}, "
            f"conversionRate={self.conversionRate}, userId={self.userId} )"
        )

    def __repr__(self):
        return (
            f"Wallet: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, coinsBalance={self.coinsBalance}, "
            f"pointsBalance={self.pointsBalance}, "
            f"conversionRate={self.conversionRate}, userId={self.userId} )"
        )

    def __eq__(self, other):
        return (
            isinstance(other, Wallet)
            and self.id == other.id
            and self.coinsBalance == other.coinsBalance
            and self.pointsBalance == other.pointsBalance
            and self.conversionRate == other.conversionRate
            and self.userId == other.userId
        )

    def __hash__(self):
        return hash(
            (self.id, self.coinsBalance, self.pointsBalance,
             self.conversionRate, self.userId)
        )
