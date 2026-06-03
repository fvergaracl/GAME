"""
DslSimulationService behavioural tests.

The service composes three pieces: the strategy lookup (tenant scoped),
the precompute, and the timeout-wrapped interpreter run. These tests
mock the strategy definition service so we never need a DB and exercise
the actual interpreter + context — that way a regression in either
shows up here too.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import DslTimeoutError, DslValidationError, NotFoundError
from app.schema.dsl_schema import InlineSimulationRequest, SimulationRequest
from app.schema.strategy_definition_schema import StrategyDefinitionRead
from app.services.dsl_simulation_service import DslSimulationService


def _read(astJson, *, status="PUBLISHED"):
    return StrategyDefinitionRead(
        id="row-1",
        realmId="realm-a",
        name="demo",
        description=None,
        type="DSL_FULL",
        parentStrategyId=None,
        astJson=astJson,
        blocklyXml=None,
        version=1,
        status=status,
        createdBy=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        publishedAt=datetime.now(timezone.utc),
        experimentTag=None,
    )


def _ast_basic():
    return {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {
                    "type": "compare",
                    "id": "c",
                    "op": "<",
                    "left": {
                        "type": "field",
                        "id": "f",
                        "path": "user.measurements_count",
                    },
                    "right": {"type": "literal", "id": "lr", "value": 2},
                },
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a1",
                        "value": {"type": "literal", "id": "lv", "value": 1},
                        "case_name": "BasicEngagement",
                    }
                ],
            },
            {
                "type": "rule",
                "id": "r2",
                "when": {"type": "literal", "id": "lt", "value": True},
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a2",
                        "value": {"type": "literal", "id": "lv2", "value": 10},
                        "case_name": "PerformanceBonus",
                    }
                ],
            },
        ],
    }


def _service(read_result=None, get_side_effect=None):
    strategy_service = MagicMock()
    if get_side_effect is not None:
        strategy_service.get_strategy = AsyncMock(side_effect=get_side_effect)
    else:
        strategy_service.get_strategy = AsyncMock(return_value=read_result)
    analytics = MagicMock()
    analytics.get_user_task_measurements_count = AsyncMock(return_value=5)
    service = DslSimulationService(strategy_service, analytics)
    return service, strategy_service, analytics


@pytest.mark.asyncio
async def test_simulate_returns_first_matching_branch():
    svc, _, _ = _service(read_result=_read(_ast_basic()))

    response = await svc.simulate(
        id="row-1",
        realmId="realm-a",
        request=SimulationRequest(
            externalGameId="g",
            externalTaskId="t",
            externalUserId="u",
            mockState={"user.measurements_count": 1},
        ),
    )

    assert response.points == 1.0
    assert response.caseName == "BasicEngagement"
    assert any(
        e.nodeId == "a1" and e.type == "assign_points" for e in response.executionTrace
    )


@pytest.mark.asyncio
async def test_simulate_falls_through_when_first_rule_misses():
    svc, _, _ = _service(read_result=_read(_ast_basic()))

    response = await svc.simulate(
        id="row-1",
        realmId="realm-a",
        request=SimulationRequest(
            externalGameId="g",
            externalTaskId="t",
            externalUserId="u",
            mockState={"user.measurements_count": 5},
        ),
    )

    assert response.points == 10.0
    assert response.caseName == "PerformanceBonus"


@pytest.mark.asyncio
async def test_simulate_calls_analytics_when_no_mock_for_path():
    svc, _, analytics = _service(read_result=_read(_ast_basic()))

    await svc.simulate(
        id="row-1",
        realmId="realm-a",
        request=SimulationRequest(
            externalGameId="g",
            externalTaskId="t",
            externalUserId="u",
        ),
    )

    analytics.get_user_task_measurements_count.assert_awaited_once_with("t", "u")


@pytest.mark.asyncio
async def test_simulate_works_on_draft():
    svc, _, _ = _service(read_result=_read(_ast_basic(), status="DRAFT"))
    response = await svc.simulate(
        id="row-1",
        realmId="realm-a",
        request=SimulationRequest(
            externalGameId="g",
            externalTaskId="t",
            externalUserId="u",
            mockState={"user.measurements_count": 1},
        ),
    )
    assert response.caseName == "BasicEngagement"


@pytest.mark.asyncio
async def test_simulate_works_on_archived():
    svc, _, _ = _service(read_result=_read(_ast_basic(), status="ARCHIVED"))
    response = await svc.simulate(
        id="row-1",
        realmId="realm-a",
        request=SimulationRequest(
            externalGameId="g",
            externalTaskId="t",
            externalUserId="u",
            mockState={"user.measurements_count": 1},
        ),
    )
    assert response.caseName == "BasicEngagement"


@pytest.mark.asyncio
async def test_simulate_rejects_missing_ast():
    svc, _, _ = _service(read_result=_read(None))
    with pytest.raises(DslValidationError, match="no AST"):
        await svc.simulate(
            id="row-1",
            realmId="realm-a",
            request=SimulationRequest(
                externalGameId="g",
                externalTaskId="t",
                externalUserId="u",
            ),
        )


@pytest.mark.asyncio
async def test_simulate_propagates_not_found_for_other_realm():
    svc, _, _ = _service(
        get_side_effect=NotFoundError(detail="Custom strategy not found")
    )
    with pytest.raises(NotFoundError):
        await svc.simulate(
            id="row-1",
            realmId="realm-other",
            request=SimulationRequest(
                externalGameId="g",
                externalTaskId="t",
                externalUserId="u",
            ),
        )


@pytest.mark.asyncio
async def test_simulate_translates_timeout_to_dsl_timeout_error():
    svc, _, _ = _service(read_result=_read(_ast_basic()))

    async def _raise_timeout(coro, *args, **kwargs):
        # Close the inner coroutine so we don't trip the "coroutine never
        # awaited" warning when forcing the timeout path.
        if hasattr(coro, "close"):
            coro.close()
        raise asyncio.TimeoutError()

    with patch(
        "app.services.dsl_simulation_service.asyncio.wait_for",
        new=_raise_timeout,
    ):
        with pytest.raises(DslTimeoutError, match="time limit"):
            await svc.simulate(
                id="row-1",
                realmId="realm-a",
                request=SimulationRequest(
                    externalGameId="g",
                    externalTaskId="t",
                    externalUserId="u",
                    mockState={"user.measurements_count": 1},
                ),
            )


# ----- Inline simulate (Sprint 5, fix C7) ----------------------------------


@pytest.mark.asyncio
async def test_simulate_inline_runs_ast_without_db_lookup():
    """Inline simulate must NOT touch the strategy definition service —
    that's the whole point of fix C7 (no orphan DRAFT rows)."""
    svc, strategy_service, _ = _service()

    response = await svc.simulate_inline(
        realmId="realm-a",
        request=InlineSimulationRequest(
            externalGameId="g",
            externalTaskId="t",
            externalUserId="u",
            astJson=_ast_basic(),
            mockState={"user.measurements_count": 1},
        ),
    )

    assert response.points == 1.0
    assert response.caseName == "BasicEngagement"
    strategy_service.get_strategy.assert_not_called()


@pytest.mark.asyncio
async def test_simulate_inline_falls_through_like_id_based():
    svc, _, _ = _service()

    response = await svc.simulate_inline(
        realmId="realm-a",
        request=InlineSimulationRequest(
            externalGameId="g",
            externalTaskId="t",
            externalUserId="u",
            astJson=_ast_basic(),
            mockState={"user.measurements_count": 5},
        ),
    )

    assert response.points == 10.0
    assert response.caseName == "PerformanceBonus"


@pytest.mark.asyncio
async def test_simulate_inline_rejects_invalid_ast():
    svc, _, _ = _service()

    with pytest.raises(DslValidationError):
        await svc.simulate_inline(
            realmId="realm-a",
            request=InlineSimulationRequest(
                externalGameId="g",
                externalTaskId="t",
                externalUserId="u",
                astJson={"type": "program", "id": "p"},
            ),
        )
