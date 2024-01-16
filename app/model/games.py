"""
CREATE TABLE Games (
  id SERIAL PRIMARY KEY, 
  externalGameID VARCHAR(255) UNIQUE,
  platform VARCHAR(255),
  endDateTime TIMESTAMP NULL
);
"""

from datetime import datetime
from app.model.base_model import BaseModel
from sqlmodel import Column, DateTime, Field, String


class Games(BaseModel, table=True):
    __tablename__ = "games"

    externalGameID: str = Field(sa_column=Column(String, unique=True))
    platform: str = Field(sa_column=Column(String))
    endDateTime: datetime = Field(sa_column=Column(
        DateTime(timezone=True), nullable=True))

    def __str__(self):
        return f"Game: {self.externalGameID}, {self.platform}, {self.endDateTime}"

    def __repr__(self):
        return f"Game: {self.externalGameID}, {self.platform}, {self.endDateTime}"

    def __eq__(self, other):
        return self.externalGameID == other.externalGameID and self.platform == other.platform and self.endDateTime == other.endDateTime

    def __hash__(self):
        return hash((self.externalGameID, self.platform, self.endDateTime))

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.endDateTime < other.endDateTime
