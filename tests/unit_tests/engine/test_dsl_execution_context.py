"""
ExecutionContext precompute tests.

The interpreter is supposed to be CPU-pure: every analytic value it
might read is fetched once, up front, by ``ExecutionContext.build_for_ast``.
These tests pin that contract: only referenced fields hit the analytics
service, and ``mock_state`` short-circuits the analytics call entirely.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.engine.dsl_execution_context import ExecutionContext


def _ast_referencing(*paths):
    fields = [{"type": "field", "path": p} for p in paths]
    # Wrap into a structure the walker can traverse.
    rules = [
        {
            "type": "rule",
            "when": {"type": "compare", "op": "==", "left": f, "right": f},
            "then": [
                {
                    "type": "assign_points",
                    "value": {"type": "literal", "value": 1},
                    "case_name": "x",
                }
            ],
        }
        for f in fields
    ]
    return {"type": "program", "rules": rules}


def _analytics_stub():
    svc = MagicMock()
    svc.get_user_task_measurements_count = AsyncMock(return_value=7)
    svc.count_measurements_by_external_task_id = AsyncMock(return_value=42)
    svc.get_avg_time_between_tasks_by_user_and_game_task = AsyncMock(
        return_value=1.5
    )
    svc.get_avg_time_between_tasks_for_all_users = AsyncMock(return_value=2.0)
    svc.get_last_window_time_diff = AsyncMock(return_value=3.0)
    svc.get_new_last_window_time_diff = AsyncMock(return_value=4.0)
    return svc


@pytest.mark.asyncio
async def test_only_referenced_paths_trigger_analytics_calls():
    svc = _analytics_stub()
    ast = _ast_referencing("user.measurements_count")

    ctx = await ExecutionContext.build_for_ast(
        ast,
        externalGameId="g",
        externalTaskId="t",
        externalUserId="u",
        data=None,
        analytics_service=svc,
    )

    svc.get_user_task_measurements_count.assert_awaited_once_with("t", "u")
    svc.count_measurements_by_external_task_id.assert_not_called()
    svc.get_avg_time_between_tasks_for_all_users.assert_not_called()
    assert ctx.resolved_fields["user.measurements_count"] == 7


@pytest.mark.asyncio
async def test_mock_state_bypasses_analytics():
    svc = _analytics_stub()
    ast = _ast_referencing("user.measurements_count", "all.avg_time")

    ctx = await ExecutionContext.build_for_ast(
        ast,
        externalGameId="g",
        externalTaskId="t",
        externalUserId="u",
        data=None,
        analytics_service=svc,
        mock_state={"user.measurements_count": 99, "all.avg_time": 0.1},
    )

    svc.get_user_task_measurements_count.assert_not_called()
    svc.get_avg_time_between_tasks_for_all_users.assert_not_called()
    assert ctx.resolved_fields["user.measurements_count"] == 99
    assert ctx.resolved_fields["all.avg_time"] == 0.1


@pytest.mark.asyncio
async def test_data_path_snapshots_payload_value():
    svc = _analytics_stub()
    ast = _ast_referencing("data.streak")

    ctx = await ExecutionContext.build_for_ast(
        ast,
        externalGameId="g",
        externalTaskId="t",
        externalUserId="u",
        data={"streak": 5},
        analytics_service=svc,
    )

    assert ctx.resolved_fields["data.streak"] == 5


@pytest.mark.asyncio
async def test_data_path_missing_key_resolves_to_none():
    svc = _analytics_stub()
    ast = _ast_referencing("data.missing")

    ctx = await ExecutionContext.build_for_ast(
        ast,
        externalGameId="g",
        externalTaskId="t",
        externalUserId="u",
        data={},
        analytics_service=svc,
    )

    assert ctx.resolved_fields["data.missing"] is None


@pytest.mark.asyncio
async def test_analytics_cache_shared_across_builds_resolves_once():
    # Sprint 13: DSL_EXTEND builds two contexts (pre + post) for the same
    # user/request. A shared analytics_cache means each analytics method
    # runs once, not once per build.
    svc = _analytics_stub()
    ast = _ast_referencing("user.measurements_count")
    cache: dict = {}

    ctx1 = await ExecutionContext.build_for_ast(
        ast,
        externalGameId="g",
        externalTaskId="t",
        externalUserId="u",
        data=None,
        analytics_service=svc,
        analytics_cache=cache,
    )
    ctx2 = await ExecutionContext.build_for_ast(
        ast,
        externalGameId="g",
        externalTaskId="t",
        externalUserId="u",
        data=None,
        analytics_service=svc,
        analytics_cache=cache,
    )

    # One DB round-trip total, despite two builds.
    svc.get_user_task_measurements_count.assert_awaited_once_with("t", "u")
    assert ctx1.resolved_fields["user.measurements_count"] == 7
    assert ctx2.resolved_fields["user.measurements_count"] == 7
    assert cache["user.measurements_count"] == 7


@pytest.mark.asyncio
async def test_without_cache_each_build_calls_analytics():
    # No shared cache → the second build re-fetches (the pre-Sprint-13
    # behaviour, still the default for DSL_FULL).
    svc = _analytics_stub()
    ast = _ast_referencing("user.measurements_count")

    for _ in range(2):
        await ExecutionContext.build_for_ast(
            ast,
            externalGameId="g",
            externalTaskId="t",
            externalUserId="u",
            data=None,
            analytics_service=svc,
        )

    assert svc.get_user_task_measurements_count.await_count == 2


@pytest.mark.asyncio
async def test_static_paths_resolve_without_analytics():
    svc = _analytics_stub()
    ast = _ast_referencing("externalGameId", "externalUserId")

    ctx = await ExecutionContext.build_for_ast(
        ast,
        externalGameId="g-1",
        externalTaskId="t-1",
        externalUserId="u-1",
        data=None,
        analytics_service=svc,
    )

    assert ctx.resolved_fields["externalGameId"] == "g-1"
    assert ctx.resolved_fields["externalUserId"] == "u-1"
    # No analytic method should have been called for static paths.
    svc.get_user_task_measurements_count.assert_not_called()
