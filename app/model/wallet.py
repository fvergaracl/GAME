"""
CREATE TABLE Wallet (
  id SERIAL PRIMARY KEY,
  coinsBalance DECIMAL(10, 2),
  pointsBalance DECIMAL(10, 2),
  conversionRate DECIMAL(10, 2),
  userId INT,
  FOREIGN KEY (userId) REFERENCES Users(id)
);

"""

from app.model.base_model import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer, Float
from app.core.config import configs


class Wallet(BaseModel, table=True):
    coinsBalance: float = Field(sa_column=Column(Float), default=0.0)
    pointsBalance: float = Field(sa_column=Column(Float), default=0.0)
    conversionRate: float = Field(sa_column=Column(
        Integer), default=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN)
    userId: int = Field(sa_column=Column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False))

    def __str__(self):
        return f"Wallet: {self.coinsBalance}, {self.pointsBalance}, {self.conversionRate}, {self.userId}"

    def __repr__(self):
        return f"Wallet: {self.coinsBalance}, {self.pointsBalance}, {self.conversionRate}, {self.userId}"

    def __eq__(self, other):
        return self.coinsBalance == other.coinsBalance and self.pointsBalance == other.pointsBalance and self.conversionRate == other.conversionRate and self.userId == other.userId

    def __hash__(self):
        return hash((self.coinsBalance, self.pointsBalance, self.conversionRate, self.userId))

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.userId < other.userId
