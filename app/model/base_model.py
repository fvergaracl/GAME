from datetime import datetime
from uuid import uuid4
from sqlmodel import Column, DateTime, Field, SQLModel, func
from sqlalchemy.dialects.postgresql import UUID


class BaseModel(SQLModel):
    id: str = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        sa_column=Column(UUID(as_uuid=True), primary_key=True, index=True)
    )
    created_at: datetime = Field(sa_column=Column(
        DateTime(timezone=True), default=func.now()))
    updated_at: datetime = Field(sa_column=Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()))
