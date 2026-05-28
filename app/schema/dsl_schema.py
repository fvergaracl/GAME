"""
Pydantic schemas for the ``/v1/strategies/custom/{id}/simulate`` endpoint.

Schema is intentionally close to the existing strategy CRUD shapes so the
frontend can reuse helpers. ``mockState`` is a flat dotted-path → value
map matching ``FIELD_RESOLVERS`` entries; unknown keys are silently
ignored, which gives Blockly the freedom to send richer payloads without
breaking older backends.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExecutionTraceEntry(BaseModel):
    """One step of the interpreter trace."""

    nodeId: Optional[str] = None
    type: str
    value: Any = None
    branch: Optional[str] = None


class SimulationRequest(BaseModel):
    externalGameId: str = Field(min_length=1, max_length=200)
    externalTaskId: str = Field(min_length=1, max_length=200)
    externalUserId: str = Field(min_length=1, max_length=200)
    data: Optional[Dict[str, Any]] = None
    mockState: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional dotted-path overrides; keys match field whitelist "
            "entries (e.g. 'user.measurements_count'). When present, the "
            "interpreter uses the mock value instead of calling analytics."
        ),
    )


class InlineSimulationRequest(SimulationRequest):
    """Sprint 5 (fix C7): dry-run an AST supplied inline.

    The id-based ``/{id}/simulate`` route loads a *persisted* strategy,
    which forced the editor to save a hidden DRAFT on every "Probar"
    click just to get an id — accumulating orphan rows in the DB. This
    request carries the AST directly so the designer can test the exact
    blocks on the canvas (including unsaved edits) without persisting
    anything.
    """

    astJson: Dict[str, Any] = Field(
        description=(
            "The strategy AST to dry-run, supplied inline so the designer "
            "can test unsaved edits without persisting a draft."
        )
    )


class SimulationResponse(BaseModel):
    points: float
    caseName: Optional[str] = None
    callbackData: Dict[str, Any] = Field(default_factory=dict)
    executionTrace: List[ExecutionTraceEntry] = Field(default_factory=list)
