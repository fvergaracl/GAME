from datetime import datetime
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, DateTime, Field, SQLModel, func, ForeignKey


class BaseModel(SQLModel):
    """
    Base model class that provides ID, creation, and update timestamps.

    Attributes:
        id (str): Unique identifier for each instance, automatically generated
         using UUID.
        created_at (datetime): Timestamp recording when an instance is created,
          set to the current time by default.
        updated_at (datetime): Timestamp recording the last update of an
          instance, set to the current time on creation and updates.

    Methods:
        __str__(self): Returns a string representation of the model instance.
        __repr__(self): Returns an official string representation of the model.
        __eq__(self, other): Determines equality based on ID, creation,
          and update timestamps.
        __hash__(self): Provides a hash based on the ID, created_at, and
          updated_at attributes.

    Configurations:
        orm_mode (bool): Allows the model to be used with ORM, set to True to
          enable.
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
    apiKey_used: str = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey(
            "apikey.apiKey"), nullable=True)
    )

    class Config:  # noqa
        orm_mode = True  # noqa

    def __str__(self):
        return (
            f"BaseModel: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at})"
        )

    def __repr__(self):
        return (
            f"BaseModel: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, BaseModel)
            and self.id == other.id
            and self.created_at == other.created_at
            and self.updated_at == other.updated_at
        )

    def __hash__(self):
        return hash((self.id, self.created_at, self.updated_at))
