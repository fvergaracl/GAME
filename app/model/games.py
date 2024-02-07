from datetime import datetime

from sqlmodel import Column, DateTime, Field, String

from app.model.base_model import BaseModel


class Games(BaseModel, table=True):
    __tablename__ = "games"

    externalGameId: str = Field(sa_column=Column(String, unique=True))
    platform: str = Field(sa_column=Column(String), nullable=False)
    endDateTime: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
