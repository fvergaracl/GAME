"""
Repository for ``StrategyExecutionLog`` rows (Sprint 11).

Writes are best-effort: the engine never blocks scoring on the audit
log, so the service layer wraps the insert in its own try/except. The
read methods power the runbook UI and the post-mortem command-line
helpers.

Sprint 10 adds aggregation queries used by the observability dashboard:
counts grouped by status / error code / case name, a percentile-friendly
sample of durations, and a time-bucketed timeseries. All of them are
single round-trips so the dashboard renders in one fetch.
"""

from contextlib import AbstractAsyncContextManager
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.strategy_execution_log import StrategyExecutionLog
from app.repository.base_repository import BaseRepository


class StrategyExecutionLogRepository(BaseRepository):
    def __init__(
        self,
        session_factory: Callable[
            ..., AbstractAsyncContextManager[AsyncSession]
        ],
        model=StrategyExecutionLog,
    ) -> None:
        super().__init__(session_factory, model)

    async def insert_row(self, row: StrategyExecutionLog) -> None:
        """
        Insert a pre-built model instance directly. Bypasses
        ``BaseRepository.create`` because we don't have a pydantic
        schema for these -- the row is assembled by the observer
        from interpreter output and persisted as-is.
        """
        async with self.session_factory() as session:
            session.add(row)
            await session.commit()

    async def list_for_strategy(
        self,
        *,
        strategyId: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[StrategyExecutionLog]:
        """
        Most-recent-first listing for the runbook view.

        ``status`` filter is the common "show me the failures" use
        case from the runbook. The result is capped at 200 so the
        JSON payload stays small even when the operator forgets to
        pass ``limit``.
        """
        stmt = (
            select(self.model)
            .where(self.model.strategyId == strategyId)
            .order_by(self.model.created_at.desc().nullslast())
        )
        if status is not None:
            stmt = stmt.where(self.model.status == status)
        stmt = stmt.limit(min(max(limit, 1), 200))
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Sprint 10 — aggregations for the dashboard observability view.
    #
    # All four queries scope by strategyId + optional time range. We hit
    # the same indexed columns (strategyId, status, created_at) so the
    # planner can use index-only scans even on large execution-log
    # tables. Each returns a plain dict/list so the service can compose
    # them into a single response without ORM-layer roundtrips.
    # ------------------------------------------------------------------

    def _apply_window(self, stmt, strategyId: str, sinceDt, untilDt):
        stmt = stmt.where(self.model.strategyId == strategyId)
        if sinceDt is not None:
            stmt = stmt.where(self.model.created_at >= sinceDt)
        if untilDt is not None:
            stmt = stmt.where(self.model.created_at <= untilDt)
        return stmt

    async def count_by_status(
        self,
        *,
        strategyId: str,
        sinceDt: Optional[datetime] = None,
        untilDt: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """Counts grouped by ``status`` (ok/error/timeout/limit)."""
        stmt = select(self.model.status, func.count()).group_by(
            self.model.status
        )
        stmt = self._apply_window(stmt, strategyId, sinceDt, untilDt)
        async with self.session_factory() as session:
            rows = (await session.execute(stmt)).all()
        return {status: int(n) for status, n in rows if status is not None}

    async def count_by_error_code(
        self,
        *,
        strategyId: str,
        sinceDt: Optional[datetime] = None,
        untilDt: Optional[datetime] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Top error codes by frequency. Most failures share one code."""
        stmt = (
            select(self.model.errorCode, func.count())
            .where(self.model.errorCode.is_not(None))
            .group_by(self.model.errorCode)
            .order_by(func.count().desc())
            .limit(min(max(limit, 1), 50))
        )
        stmt = self._apply_window(stmt, strategyId, sinceDt, untilDt)
        async with self.session_factory() as session:
            rows = (await session.execute(stmt)).all()
        return [{"code": code, "count": int(n)} for code, n in rows]

    async def count_by_case_name(
        self,
        *,
        strategyId: str,
        sinceDt: Optional[datetime] = None,
        untilDt: Optional[datetime] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Which rule cases the strategy is firing — null caseName = no
        rule matched (fell back to defaultPoints)."""
        stmt = (
            select(self.model.caseName, func.count())
            .group_by(self.model.caseName)
            .order_by(func.count().desc())
            .limit(min(max(limit, 1), 50))
        )
        stmt = self._apply_window(stmt, strategyId, sinceDt, untilDt)
        async with self.session_factory() as session:
            rows = (await session.execute(stmt)).all()
        return [
            {"caseName": case, "count": int(n)} for case, n in rows
        ]

    async def duration_and_nodes_summary(
        self,
        *,
        strategyId: str,
        sinceDt: Optional[datetime] = None,
        untilDt: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Summary stats: count, avg/min/max/sum for duration and nodes,
        plus sum of points. Percentiles are computed in Python from a
        bounded sample because some backends (SQLite, used in tests)
        don't support ``percentile_cont``.
        """
        stmt = select(
            func.count(),
            func.avg(self.model.durationMs),
            func.min(self.model.durationMs),
            func.max(self.model.durationMs),
            func.sum(self.model.durationMs),
            func.avg(self.model.nodesExecuted),
            func.max(self.model.nodesExecuted),
            func.sum(self.model.points),
        )
        stmt = self._apply_window(stmt, strategyId, sinceDt, untilDt)
        async with self.session_factory() as session:
            row = (await session.execute(stmt)).one()
        return {
            "count": int(row[0] or 0),
            "durationAvgMs": float(row[1]) if row[1] is not None else 0.0,
            "durationMinMs": float(row[2]) if row[2] is not None else 0.0,
            "durationMaxMs": float(row[3]) if row[3] is not None else 0.0,
            "durationSumMs": float(row[4]) if row[4] is not None else 0.0,
            "nodesAvg": float(row[5]) if row[5] is not None else 0.0,
            "nodesMax": int(row[6]) if row[6] is not None else 0,
            "pointsSum": float(row[7]) if row[7] is not None else 0.0,
        }

    async def sample_durations(
        self,
        *,
        strategyId: str,
        sinceDt: Optional[datetime] = None,
        untilDt: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[float]:
        """
        Sample of raw durations used to compute p50/p95/p99 in the
        service layer. Bounded at 1000 rows so we don't fetch the whole
        log when a busy strategy has millions of entries — that yields
        ±2% accuracy on p95 which is fine for the UI.
        """
        stmt = (
            select(self.model.durationMs)
            .where(self.model.durationMs.is_not(None))
            .order_by(self.model.created_at.desc().nullslast())
            .limit(min(max(limit, 1), 5000))
        )
        stmt = self._apply_window(stmt, strategyId, sinceDt, untilDt)
        async with self.session_factory() as session:
            rows = (await session.execute(stmt)).all()
        return [float(r[0]) for r in rows if r[0] is not None]

    async def sample_points(
        self,
        *,
        strategyId: str,
        sinceDt: Optional[datetime] = None,
        untilDt: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[float]:
        """Sample of awarded points. Powers the points-distribution
        histogram. ``points`` is null on failed runs so we filter those."""
        stmt = (
            select(self.model.points)
            .where(self.model.points.is_not(None))
            .order_by(self.model.created_at.desc().nullslast())
            .limit(min(max(limit, 1), 5000))
        )
        stmt = self._apply_window(stmt, strategyId, sinceDt, untilDt)
        async with self.session_factory() as session:
            rows = (await session.execute(stmt)).all()
        return [float(r[0]) for r in rows if r[0] is not None]
