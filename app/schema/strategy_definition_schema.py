"""
Pydantic schemas for the persistent strategy model (Sprint 3).

Three layers:
  * ``Create…`` – input payload for ``POST /v1/strategies/custom``.
  * ``Update…`` – input payload for ``PUT /v1/strategies/custom/{id}``.
    Editing a published row forks a new draft instead of mutating it; the
    business rule lives in the service.
  * ``…Read`` – outbound representation returned by every endpoint.

The internal persistence schema (``StrategyDefinitionPersist``) mirrors
the SQL row plus tenant scoping resolved server-side, so endpoints never
let the caller pick its own ``realmId`` / ``createdBy``.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.model.strategy_definition import (
    StrategyDefinitionStatus,
    StrategyDefinitionType,
)


class StrategyDefinitionCreate(BaseModel):
    """Caller-supplied payload for a brand-new strategy (always v1, DRAFT)."""

    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    type: StrategyDefinitionType = Field(
        default=StrategyDefinitionType.DSL_FULL,
        description=(
            "DSL_FULL replaces the parent; DSL_EXTEND wraps a built-in "
            "with pre/post rules."
        ),
    )
    parentStrategyId: Optional[str] = Field(
        default=None,
        description=(
            "Required when type=DSL_EXTEND. Must reference an existing "
            "built-in strategy id (e.g. 'default')."
        ),
    )
    astJson: Optional[dict] = None
    blocklyXml: Optional[str] = None
    experimentTag: Optional[str] = Field(default=None, max_length=200)


class StrategyDefinitionUpdate(BaseModel):
    """
    PUT payload. Fields left ``None`` are kept as-is.

    When the target row is ``PUBLISHED`` the service forks a new draft at
    ``version + 1`` and applies the patch to the fork; the published row
    keeps running.
    """

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    type: Optional[StrategyDefinitionType] = None
    parentStrategyId: Optional[str] = None
    astJson: Optional[dict] = None
    blocklyXml: Optional[str] = None
    experimentTag: Optional[str] = Field(default=None, max_length=200)


class StrategyDefinitionRead(BaseModel):
    """Outbound view of a strategy row."""

    id: str
    realmId: Optional[str] = None
    name: str
    description: Optional[str] = None
    type: str
    parentStrategyId: Optional[str] = None
    astJson: Optional[dict] = None
    blocklyXml: Optional[str] = None
    version: int
    status: str
    createdBy: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    publishedAt: Optional[datetime] = None
    experimentTag: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StrategyDefinitionPersist(BaseModel):
    """
    Internal schema used by the repository layer to persist a row.

    Endpoints never accept this directly; the service constructs it from a
    validated public payload plus the resolved tenant scope.
    """

    realmId: Optional[str] = None
    name: str
    description: Optional[str] = None
    type: str = StrategyDefinitionType.DSL_FULL.value
    parentStrategyId: Optional[str] = None
    astJson: Optional[dict] = None
    blocklyXml: Optional[str] = None
    version: int = 1
    status: str = StrategyDefinitionStatus.DRAFT.value
    createdBy: Optional[str] = None
    publishedAt: Optional[datetime] = None
    experimentTag: Optional[str] = None
    apiKey_used: Optional[str] = None
    oauth_user_id: Optional[str] = None
