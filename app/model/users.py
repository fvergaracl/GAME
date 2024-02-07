"""
CREATE TABLE Users (
  id SERIAL PRIMARY KEY,
  externalUserId VARCHAR(255) UNIQUE NOT NULL
);
"""

from sqlmodel import Column, Field, String

from app.model.base_model import BaseModel


class Users(BaseModel, table=True):
    externalUserId: str = Field(sa_column=Column(String, unique=True))

    def __str__(self):
        return f"User: {self.externalUserId}"

    def __repr__(self):
        return f"User: {self.externalUserId}"

    def __eq__(self, other):
        return self.externalUserId == other.externalUserId

    def __hash__(self):
        return hash((self.externalUserId))

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.externalUserId < other.externalUserId
