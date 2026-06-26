"""
Sprint 10 - integration tests for the aggregation queries on
``StrategyExecutionLogRepository``.

Runs the real repository against the in-memory aiosqlite engine the
existing repository test suite uses (see ``conftest.py``). Verifies
that the SQL the service relies on is valid - type coercion (Numeric
→ float, Integer → int), grouping, ordering, and the time-window
filter all behave as the service expects.
"""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

# Force model registration before SQLModel.metadata.create_all runs in
# the shared async_engine fixture. The conftest imports most models
# eagerly but not StrategyExecutionLog, so without this side-effect
# import the ``strategyexecutionlog`` table wouldn't exist.
import app.model.strategy_execution_log  # noqa: F401
from app.model.strategy_execution_log import StrategyExecutionLog
from app.repository.strategy_execution_log_repository import (
    StrategyExecutionLogRepository,
)


@pytest_asyncio.fixture
async def repo(session_factory):
    return StrategyExecutionLogRepository(session_factory)


@pytest_asyncio.fixture
async def seeded(repo):
    """
    Seed a deterministic mix of executions for strategy s1 + one row
    for s2 so we can prove tenant scoping holds in the aggregations.
    """
    base = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
    rows = [
        # 6 ok runs, 2 errors, 1 timeout on s1.
        ("s1", "ok", None, 10.0, 1.0, "CaseA", base),
        ("s1", "ok", None, 20.0, 2.0, "CaseA", base + timedelta(minutes=1)),
        ("s1", "ok", None, 30.0, 3.0, "CaseB", base + timedelta(minutes=2)),
        ("s1", "ok", None, 40.0, 4.0, None, base + timedelta(minutes=3)),
        ("s1", "ok", None, 50.0, 5.0, "CaseA", base + timedelta(minutes=4)),
        ("s1", "ok", None, 60.0, 6.0, "CaseA", base + timedelta(minutes=5)),
        (
            "s1",
            "error",
            "DSL_ARITH_DIV_BY_ZERO",
            5.0,
            None,
            None,
            base + timedelta(minutes=6),
        ),
        (
            "s1",
            "error",
            "DSL_FIELD_MISSING",
            7.0,
            None,
            None,
            base + timedelta(minutes=7),
        ),
        (
            "s1",
            "timeout",
            "DSL_TIMEOUT",
            999.0,
            None,
            None,
            base + timedelta(minutes=8),
        ),
        # Unrelated strategy - must not bleed into s1's aggregates.
        ("s2", "ok", None, 1.0, 1.0, "Other", base),
    ]
    for strat_id, status, code, dur, pts, case, ts in rows:
        await repo.insert_row(
            StrategyExecutionLog(
                strategyId=strat_id,
                strategyVersion=1,
                strategyType="DSL_FULL",
                realmId="realm-a",
                externalGameId=None,
                externalTaskId=None,
                externalUserId=None,
                status=status,
                errorCode=code,
                points=pts,
                caseName=case,
                durationMs=dur,
                nodesExecuted=5,
                trace=None,
                sampled=status == "ok",
                parentStrategyId=None,
                notes=None,
                created_at=ts,
            )
        )
    return base


@pytest.mark.asyncio
async def test_count_by_status_groups_only_target_strategy(repo, seeded):
    out = await repo.count_by_status(strategyId="s1")
    assert out == {"ok": 6, "error": 2, "timeout": 1}


@pytest.mark.asyncio
async def test_count_by_error_code_filters_nulls_desc(repo, seeded):
    out = await repo.count_by_error_code(strategyId="s1")
    # Top-N ordering: ties broken by SQL order, but the codes returned
    # must only be the non-null ones from s1.
    codes = {row["code"]: row["count"] for row in out}
    assert codes == {
        "DSL_ARITH_DIV_BY_ZERO": 1,
        "DSL_FIELD_MISSING": 1,
        "DSL_TIMEOUT": 1,
    }


@pytest.mark.asyncio
async def test_count_by_case_name_includes_default_null_bucket(repo, seeded):
    out = await repo.count_by_case_name(strategyId="s1")
    counts = {row["caseName"]: row["count"] for row in out}
    # CaseA fired 4×, CaseB 1×, the rest land in the null bucket the
    # dashboard renders as "(default)": 1 OK run with no case + 2
    # errors + 1 timeout = 4.
    assert counts["CaseA"] == 4
    assert counts["CaseB"] == 1
    assert counts[None] == 4


@pytest.mark.asyncio
async def test_duration_and_nodes_summary_numeric_types(repo, seeded):
    out = await repo.duration_and_nodes_summary(strategyId="s1")
    # Count is the *number of rows* for this strategy, not just OK ones
    # - used by the service to compute success rate from the breakdown.
    assert out["count"] == 9
    # max duration is the timeout row.
    assert out["durationMaxMs"] == pytest.approx(999.0)
    # Points sum only includes the 6 OK runs (1+2+3+4+5+6 = 21).
    assert out["pointsSum"] == pytest.approx(21.0)


@pytest.mark.asyncio
async def test_sample_durations_returns_floats_only(repo, seeded):
    out = await repo.sample_durations(strategyId="s1")
    # All 9 rows have a duration; the order is "most recent first" but
    # the service sorts again before computing percentiles, so we only
    # assert the count + type here.
    assert len(out) == 9
    assert all(isinstance(v, float) for v in out)


@pytest.mark.asyncio
async def test_sample_points_filters_null_points(repo, seeded):
    # Only the 6 OK runs have a non-null points value; errors are nulled
    # out at the model level.
    out = await repo.sample_points(strategyId="s1")
    assert len(out) == 6
    assert sorted(out) == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


@pytest.mark.asyncio
async def test_time_window_filter_excludes_rows_before_since(repo, seeded):
    # Only keep rows from the 6th minute onwards - the four errors +
    # timeout, not the OK runs.
    cutoff = seeded + timedelta(minutes=6)
    out = await repo.count_by_status(strategyId="s1", sinceDt=cutoff)
    assert out == {"error": 2, "timeout": 1}


@pytest.mark.asyncio
async def test_aggregations_scope_to_strategy_id(repo, seeded):
    out = await repo.count_by_status(strategyId="s2")
    assert out == {"ok": 1}
