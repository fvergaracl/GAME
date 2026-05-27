"""
Persistent model for user-authored strategies.

The legacy engine (see :mod:`app.engine`) loads ``BaseStrategy`` subclasses
discovered at import time. Sprint 3 introduces a second path: strategies
expressed as a JSON AST and stored per-tenant in Postgres, so that game
designers can create or extend strategies from the dashboard without
touching Python code.

This model only stores the **definition**. Execution lives in the DSL
interpreter that lands in Sprint 4. Until then, ``astJson`` is opaque to
the engine and rows are addressable via the ``custom:<id>`` prefix on
``Games.strategyId`` / ``Tasks.strategyId`` (see the compat layer in
:mod:`app.services.strategy_service`).
"""

from enum import Enum
from typing import Optional

from datetime import datetime
from pydantic import ConfigDict
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, DateTime, Field, Integer, String, Text

from app.model.base_model import BaseModel


class StrategyDefinitionType(str, Enum):
    """
    Discriminator describing how the row should be executed.

    * ``BUILT_IN`` – placeholder for promoting a registry class into the DB,
      currently unused but kept so the column is forward-compatible.
    * ``DSL_EXTEND`` – runs a built-in parent and wraps it with pre/post
      rules expressed in the AST.
    * ``DSL_FULL`` – fully replaces the parent; only the AST runs.
    """

    BUILT_IN = "BUILT_IN"
    DSL_EXTEND = "DSL_EXTEND"
    DSL_FULL = "DSL_FULL"


class StrategyDefinitionStatus(str, Enum):
    """
    Lifecycle states. Only ``PUBLISHED`` rows are eligible to execute in
    production; ``DRAFT`` and ``ARCHIVED`` are visible from the editor but
    ignored by the engine.
    """

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class StrategyDefinition(BaseModel, table=True):
    """
    Tenant-scoped strategy authored from the dashboard.

    Versioning rules (enforced by :mod:`StrategyDefinitionService`):
      * Editing a ``PUBLISHED`` row never overwrites it. A new row with
        ``version + 1`` and ``status=DRAFT`` is created instead.
      * Publishing a draft transitions its status to ``PUBLISHED`` and
        archives any sibling row in the same ``(realmId, name)`` family
        that was previously published.
      * The ``(realmId, name, version)`` triple is unique so that the
        history can be walked deterministically.
    """

    __table_args__ = (
        UniqueConstraint(
            "realmId",
            "name",
            "version",
            name="uq_strategydefinition_realm_name_version",
        ),
    )

    realmId: Optional[str] = Field(
        default=None,
        sa_column=Column(String, nullable=True, index=True),
    )
    name: str = Field(sa_column=Column(String, nullable=False))
    description: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    type: str = Field(
        sa_column=Column(
            String,
            nullable=False,
            default=StrategyDefinitionType.DSL_FULL.value,
        )
    )
    parentStrategyId: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    astJson: Optional[dict] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    blocklyXml: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    version: int = Field(
        sa_column=Column(Integer, nullable=False, default=1)
    )
    status: str = Field(
        sa_column=Column(
            String,
            nullable=False,
            default=StrategyDefinitionStatus.DRAFT.value,
            index=True,
        )
    )
    createdBy: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    publishedAt: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    # Reserved for the experimentation work flagged in the Sprint 3 risk
    # notes: tagging a strategy lets us A/B route users between two
    # versions later without another migration. Unused for now.
    experimentTag: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )

    model_config = ConfigDict(from_attributes=True)

    def __str__(self) -> str:
        return (
            f"StrategyDefinition(id={self.id}, realmId={self.realmId}, "
            f"name={self.name}, version={self.version}, "
            f"status={self.status}, type={self.type})"
        )

    def __repr__(self) -> str:
        return self.__str__()
