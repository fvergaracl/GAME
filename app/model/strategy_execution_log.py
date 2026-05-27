"""
Sampled persistence of DSL strategy executions (Sprint 11).

Every call to ``DslStrategy.calculate_points`` produces a result + a node
trace + a duration. Persisting *all* of them would inflate the database
in production (the engine processes high-volume scoring events), so a
sampler chooses a fraction of OK runs and ALL failures to keep around
for audit + post-mortem of "why did this strategy emit X points?".

The trace itself is the same dict the interpreter already builds via
``_RunState.trace``; it is stored as JSONB to keep it queryable.
"""

from typing import Optional

from pydantic import ConfigDict
from sqlalchemy import Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Integer, Numeric, String, Text

from app.model.base_model import BaseModel


class StrategyExecutionLog(BaseModel, table=True):
    """
    One row per *sampled* DSL execution.

    Attributes:
        strategyId (str): UUID of the ``StrategyDefinition`` row that
          executed. Stored as plain string (no FK) so a strategy can be
          hard-deleted without cascading away its audit history.
        strategyVersion (int): Snapshot of the version at execution
          time; together with strategyId pins the AST that ran even if
          the row was later edited to v+1.
        strategyType (str): ``DSL_FULL`` or ``DSL_EXTEND`` -- helps
          partition dashboards by execution flavour.
        realmId (str): Tenant. Indexed for per-realm queries from the
          runbook ("show me the last failed run of strategy X").
        externalGameId/externalTaskId/externalUserId (str): The scoring
          event coordinates. Kept verbatim so an admin can reproduce
          the run via ``/simulate``.
        status (str): ``ok`` / ``error`` / ``timeout`` / ``limit``.
        errorCode (str): ``DSL_*`` code from ``app/core/exceptions.py``
          when ``status != ok``; nullable otherwise.
        points (numeric): Computed points; nullable when status != ok.
        caseName (str): ``case_name`` returned to the caller.
        durationMs (numeric): Wall-clock duration in milliseconds.
        nodesExecuted (int): Count of AST nodes visited; used to spot
          runaway rules even within the 1000-node hard cap.
        trace (jsonb): Same per-node trace the simulate endpoint
          returns -- node ids, evaluated branches, intermediate values.
          Bounded by the interpreter's node cap so the column stays
          small enough for JSONB.
        sampled (bool): True for rows that came in via the sampler,
          False for rows persisted because the run failed (errors are
          always kept regardless of the sample rate).
        parentStrategyId (str): For ``DSL_EXTEND`` runs, the built-in
          strategy id wrapped. Nullable for ``DSL_FULL``.
    """

    strategyId: str = Field(
        sa_column=Column(String, nullable=False, index=True)
    )
    strategyVersion: int = Field(sa_column=Column(Integer, nullable=False))
    strategyType: str = Field(sa_column=Column(String, nullable=False))
    realmId: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True, index=True)
    )
    externalGameId: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    externalTaskId: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    externalUserId: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    status: str = Field(
        sa_column=Column(String, nullable=False, index=True)
    )
    errorCode: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    points: Optional[float] = Field(
        default=None, sa_column=Column(Numeric, nullable=True)
    )
    caseName: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    durationMs: float = Field(sa_column=Column(Numeric, nullable=False))
    nodesExecuted: int = Field(sa_column=Column(Integer, nullable=False))
    trace: Optional[list] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    sampled: bool = Field(
        sa_column=Column(
            Boolean(), nullable=False, default=False, index=True
        )
    )
    parentStrategyId: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    notes: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    model_config = ConfigDict(from_attributes=True)

    def __str__(self) -> str:
        return (
            f"StrategyExecutionLog(id={self.id}, "
            f"strategyId={self.strategyId}, v={self.strategyVersion}, "
            f"status={self.status}, durationMs={self.durationMs}, "
            f"sampled={self.sampled})"
        )

    def __repr__(self) -> str:
        return self.__str__()
