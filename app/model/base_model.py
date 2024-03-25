from datetime import datetime
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, DateTime, Field, SQLModel, func


class BaseModel(SQLModel):
    """
    Base model class that provides common functionality for all models.
    """

    id: str = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        sa_column=Column(UUID(as_uuid=True), primary_key=True, index=True),
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), default=func.now(), onupdate=func.now()
        )
    )

    class Config:  # noqa
        orm_mode = True  # noqa

    def __str__(self):
        return f"BaseModel: (id={self.id}, created_at={self.created_at}, updated_at={self.updated_at})"

    def __repr__(self):
        return f"BaseModel: (id={self.id}, created_at={self.created_at}, updated_at={self.updated_at})"

    def __eq__(self, other):
        return (
            isinstance(other, BaseModel)
            and self.id == other.id
            and self.created_at == other.created_at
            and self.updated_at == other.updated_at
        )

    def __hash__(self):
        return hash((self.id, self.created_at, self.updated_at))
