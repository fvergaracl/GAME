"""
CREATE TABLE Users (
  id SERIAL PRIMARY KEY,
  externalUserID VARCHAR(255) UNIQUE NOT NULL
);
"""

from app.model.base_model import BaseModel
from sqlmodel import Column, Field, String


class Users(BaseModel, table=True):
    externalUserID: str = Field(sa_column=Column(String, unique=True))

    def __str__(self):
        return f"User: {self.externalUserID}"

    def __repr__(self):
        return f"User: {self.externalUserID}"

    def __eq__(self, other):
        return self.externalUserID == other.externalUserID

    def __hash__(self):
        return hash((self.externalUserID))

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.externalUserID < other.externalUserID