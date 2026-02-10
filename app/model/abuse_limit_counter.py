from datetime import datetime
from uuid import uuid4

from sqlalchemy import Index, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, DateTime, Field, SQLModel, String, func


class AbuseLimitCounter(SQLModel, table=True):
    """
    Stores per-scope counters used by abuse-prevention and rate-limiting rules.

    The tuple (scopeType, scopeValue, windowName, windowStart) is unique and
    represents one logical bucket.
    """

    __tablename__ = "abuse_limit_counter"
    __table_args__ = (
        UniqueConstraint(
            "scopeType",
            "scopeValue",
            "windowName",
            "windowStart",
            name="uq_abuse_limit_counter_scope_window",
        ),
        Index(
            "ix_abuse_limit_counter_lookup",
            "scopeType",
            "scopeValue",
            "windowName",
            "windowStart",
        ),
    )

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
    scopeType: str = Field(sa_column=Column(String, nullable=False))
    scopeValue: str = Field(sa_column=Column(String, nullable=False))
    windowName: str = Field(sa_column=Column(String, nullable=False))
    windowStart: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    counter: int = Field(sa_column=Column(Integer, nullable=False, default=0))

    class Config:
        orm_mode = True

    def __str__(self):
        return (
            "AbuseLimitCounter: "
            f"(id={self.id}, scopeType={self.scopeType}, scopeValue={self.scopeValue}, "
            f"windowName={self.windowName}, windowStart={self.windowStart}, "
            f"counter={self.counter})"
        )

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return (
            isinstance(other, AbuseLimitCounter)
            and self.scopeType == other.scopeType
            and self.scopeValue == other.scopeValue
            and self.windowName == other.windowName
            and self.windowStart == other.windowStart
            and self.counter == other.counter
        )
