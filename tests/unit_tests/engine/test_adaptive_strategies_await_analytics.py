"""Regression guard: adaptive built-ins must AWAIT their async dependencies.

``default``, ``socio_bee``, ``greengageStrategy`` and ``constantEffortStrategy``
read user history through ``UserPointsAnalyticsService`` (and greengage also
through ``TaskService``), whose methods are ``async def``. Calling one without
``await`` leaves a coroutine where a number is expected, so the next comparison
raises ``TypeError`` at runtime - a fault a *synchronous* mock hides but the
real async service does not.

These tests drive each strategy against the **real** analytics service (backed
by an ``AsyncMock`` repository, so its methods stay genuinely async), so a
regression back to an un-awaited call fails here instead of in production. They
deliberately exercise only the first branch of each strategy; the full decision
trees are covered by the per-strategy suites.
"""

from unittest.mock import AsyncMock

import pytest

from app.services.user_points_analytics_service import UserPointsAnalyticsService


def _real_analytics(**returns) -> UserPointsAnalyticsService:
    """A real ``UserPointsAnalyticsService`` over an ``AsyncMock`` repository.

    The service methods stay genuinely async (the production contract); the
    repository they delegate to returns the supplied scalars when awaited.
    """
    repo = AsyncMock()
    for name, value in returns.items():
        getattr(repo, name).return_value = value
    return UserPointsAnalyticsService(repo)


@pytest.mark.asyncio
async def test_default_awaits_analytics_basic_engagement():
    from app.engine.default import EnhancedGamificationStrategy

    strategy = EnhancedGamificationStrategy()
    strategy.debug = False
    strategy.user_points_analytics_service = _real_analytics(
        count_measurements_by_external_task_id=1
    )

    assert await strategy.calculate_points("g", "t", "u") == (1, "BasicEngagement")


@pytest.mark.asyncio
async def test_socio_bee_awaits_analytics_basic_engagement():
    from app.engine.socio_bee import SocioBeeStrategy

    strategy = SocioBeeStrategy()
    strategy.debug = False
    strategy.user_points_analytics_service = _real_analytics(
        count_measurements_by_external_task_id=1
    )

    assert await strategy.calculate_points("g", "t", "u") == (1, "BasicEngagement")


@pytest.mark.asyncio
async def test_constant_effort_awaits_analytics_basic_reward():
    from app.engine.constantEffortStrategy import ConstantEffortStrategy

    strategy = ConstantEffortStrategy()
    strategy.debug = False
    strategy.user_points_analytics_service = _real_analytics(
        get_user_task_measurements_count_the_last_seconds=0
    )

    assert await strategy.calculate_points("g", "t", "u") == (1, "BasicReward")


@pytest.mark.asyncio
async def test_greengage_awaits_analytics_and_task_params():
    from app.engine.greengageStrategy import GREENGAGEGamificationStrategy

    strategy = GREENGAGEGamificationStrategy()
    strategy.debug = False
    # get_task_params_by_externalTaskId is async too, so it must be awaited.
    strategy.task_service = AsyncMock()
    strategy.task_service.get_task_params_by_externalTaskId.return_value = []
    strategy.user_points_analytics_service = _real_analytics(
        user_has_record_before_in_externalTaskId_last_min=False
    )

    assert await strategy.calculate_points("g", "t", "u", data={"minutes": 0}) == (
        10,
        "Case 1.1 (DP)",
    )
