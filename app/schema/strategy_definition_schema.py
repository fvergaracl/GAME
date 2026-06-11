"""
Pydantic schemas for the persistent strategy model.

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

from app.model.strategy_definition import (StrategyDefinitionStatus,
                                           StrategyDefinitionType)


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


class StrategyUsageGame(BaseModel):
    """A game directly assigned to the strategy (reverse lookup)."""

    gameId: str
    externalGameId: Optional[str] = None
    platform: Optional[str] = None


class StrategyUsageTask(BaseModel):
    """A task whose strategy overrides its game's default."""

    taskId: str
    externalTaskId: Optional[str] = None
    gameId: Optional[str] = None
    externalGameId: Optional[str] = None


class StrategyUsageRead(BaseModel):
    """
    Reverse-lookup payload for ``GET /strategies/custom/{id}/usage``.

    Answers "which games/tasks run this exact strategy version" so the
    dashboard can show the blast radius before an admin reassigns,
    archives or rolls back a strategy. ``strategyId`` is the assignable
    id (``custom:<uuid>``) - the value actually stored on the consumers,
    not the bare definition id.
    """

    strategyId: str
    name: str
    version: int
    status: str
    gameCount: int
    taskCount: int
    games: list[StrategyUsageGame] = Field(default_factory=list)
    tasks: list[StrategyUsageTask] = Field(default_factory=list)


class StrategyTemplateRead(BaseModel):
    """
    Outbound view of a built-in user-facing template.

    Templates live on disk under ``app/engine/dsl_templates/user/`` and
    seed the "Usar una plantilla" path in the Blockly editor. They are
    NOT persisted rows - the editor copies the AST + blocklyXml into a
    fresh DRAFT when the designer picks one. The shape mirrors what the
    file format is so the loader can `model_validate` each JSON directly.
    """

    id: str
    name: str
    description: Optional[str] = None
    type: StrategyDefinitionType = StrategyDefinitionType.DSL_FULL
    parentStrategyId: Optional[str] = None
    astJson: dict
    blocklyXml: str


class StrategyDefinitionImport(BaseModel):
    """
    Input payload for ``POST /v1/strategies/custom/import``.

    Matches the bundle produced by the dashboard's "Exportar JSON" action
    so an export → import round-trip lands a structurally identical
    strategy. Differs from :class:`StrategyDefinitionCreate` in two ways:

      * ``astJson`` is required (the whole point of importing is the AST).
      * ``blocklyXml`` is required so the imported strategy is editable in
        the visual editor - a bare-AST import would leave a useless blank
        workspace.

    Unknown keys (``exportedAt``, ``exportedFromVersion``) are ignored so
    operator tooling can stamp metadata on exports without breaking the
    server contract.
    """

    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    type: StrategyDefinitionType = Field(
        default=StrategyDefinitionType.DSL_FULL,
    )
    parentStrategyId: Optional[str] = None
    astJson: dict
    blocklyXml: str = Field(min_length=1)
    experimentTag: Optional[str] = Field(default=None, max_length=200)

    model_config = ConfigDict(extra="ignore")


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
