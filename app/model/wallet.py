

from app.model.base_model import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer, Float
from app.core.config import configs
from sqlalchemy.dialects.postgresql import UUID


class Wallet(BaseModel, table=True):
    coinsBalance: float = Field(sa_column=Column(Float), default=0.0)
    pointsBalance: float = Field(sa_column=Column(Float), default=0.0)
    conversionRate: float = Field(sa_column=Column(
        Integer), default=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN)
    userId: str = Field(sa_column=Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )
    )

    def __str__(self):
        return f"Wallet: (id={self.id}, created_at={self.created_at}, "
    "updated_at={self.updated_at}, coinsBalance={self.coinsBalance}, "
    "pointsBalance={self.pointsBalance}, "
    "conversionRate={self.conversionRate}, userId={self.userId} )"

    def __repr__(self):
        return f"Wallet: (id={self.id}, created_at={self.created_at}, "
    "updated_at={self.updated_at}, coinsBalance={self.coinsBalance}, "
    "pointsBalance={self.pointsBalance}, "
    "conversionRate={self.conversionRate}, userId={self.userId} )"

    def __eq__(self, other):
        return (
            self.coinsBalance == other.coinsBalance and
            self.pointsBalance == other.pointsBalance and
            self.conversionRate == other.conversionRate and
            self.userId == other.userId
        )

    def __hash__(self):
        return hash(
            (self.coinsBalance, self.pointsBalance, self.conversionRate,
             self.userId)

        )

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.userId < other.userId

    def __le__(self, other):
        return self.userId <= other.userId

    def __gt__(self, other):
        return self.userId > other.userId
