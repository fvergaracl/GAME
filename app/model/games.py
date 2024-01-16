
from datetime import datetime
from app.model.base_model import BaseModel
from sqlmodel import Column, DateTime, Field, String


class Games(BaseModel, table=True):
    __tablename__ = "games"

    externalGameID: str = Field(sa_column=Column(String, unique=True))
    platform: str = Field(sa_column=Column(String), nullable=False)
    endDateTime: datetime = Field(sa_column=Column(
        DateTime(timezone=True), nullable=True))
