from unittest.mock import MagicMock

import pytest

from app.engine.socio_bee import SocioBeeStrategy


@pytest.fixture
def strategy():
    instance = SocioBeeStrategy()
    instance.debug = False
    instance.task_service = MagicMock()
    instance.user_points_service = MagicMock()
    return instance


def _set_shared_values(strategy, *, task_count=3, user_count=3, user_avg=10, all_avg=5):
    service = strategy.user_points_service
    service.count_measurements_by_external_task_id.return_value = task_count
    service.get_user_task_measurements_count.return_value = user_count
    service.get_avg_time_between_tasks_by_user_and_game_task.return_value = user_avg
    service.get_avg_time_between_tasks_for_all_users.return_value = all_avg


@pytest.mark.asyncio
async def test_calculate_points_returns_basic_engagement_when_task_count_is_less_than_two(
    strategy,
):
    strategy.user_points_service.count_measurements_by_external_task_id.return_value = 1

    points, status = await strategy.calculate_points("game_id", "task_id", "user_id")

    assert points == strategy.variable_basic_points
    assert status == "BasicEngagement"
    strategy.user_points_service.get_user_task_measurements_count.assert_not_called()


@pytest.mark.asyncio
async def test_calculate_points_returns_default_when_user_measurements_are_two_or_less(
    strategy,
):
    _set_shared_values(strategy, task_count=3, user_count=2)

    points, status = await strategy.calculate_points("game_id", "task_id", "user_id")

    assert points == strategy.default_points_task_campaign
    assert status == "default"


@pytest.mark.asyncio
async def test_calculate_points_returns_performance_bonus_when_user_avg_is_better(strategy):
    _set_shared_values(strategy, user_avg=5, all_avg=10)

    points, status = await strategy.calculate_points("game_id", "task_id", "user_id")

    assert points == strategy.variable_basic_points + strategy.variable_bonus_points
    assert status == "PerformanceBonus"
    strategy.user_points_service.get_last_window_time_diff.assert_not_called()


@pytest.mark.asyncio
async def test_calculate_points_returns_individual_over_global(strategy):
    _set_shared_values(strategy, user_avg=10, all_avg=5)
    strategy.user_points_service.get_last_window_time_diff.return_value = 3
    strategy.user_points_service.get_new_last_window_time_diff.return_value = 5

    points, status = await strategy.calculate_points("game_id", "task_id", "user_id")

    assert points == strategy.variable_individual_over_global_points
    assert status == "IndividualOverGlobal"


@pytest.mark.asyncio
async def test_calculate_points_returns_peak_performer_bonus(strategy):
    _set_shared_values(strategy, user_avg=10, all_avg=5)
    strategy.user_points_service.get_last_window_time_diff.return_value = 2
    strategy.user_points_service.get_new_last_window_time_diff.return_value = 9

    points, status = await strategy.calculate_points("game_id", "task_id", "user_id")

    assert points == strategy.variable_peak_performer_bonus_points
    assert status == "PeakPerformerBonus"


@pytest.mark.asyncio
async def test_calculate_points_returns_global_advantage_adjustment(strategy):
    _set_shared_values(strategy, user_avg=10, all_avg=7)
    strategy.user_points_service.get_last_window_time_diff.return_value = 1
    strategy.user_points_service.get_new_last_window_time_diff.return_value = 13

    points, status = await strategy.calculate_points("game_id", "task_id", "user_id")

    assert points == strategy.variable_global_advantage_adjustment_points
    assert status == "GlobalAdvantageAdjustment"


@pytest.mark.asyncio
async def test_calculate_points_returns_individual_adjustment_for_negative_diff(strategy):
    _set_shared_values(strategy, user_avg=10, all_avg=5)
    strategy.user_points_service.get_last_window_time_diff.return_value = 5
    strategy.user_points_service.get_new_last_window_time_diff.return_value = 3

    points, status = await strategy.calculate_points("game_id", "task_id", "user_id")

    assert points == strategy.variable_individual_adjustment_points
    assert status == "IndividualAdjustment"


@pytest.mark.asyncio
async def test_calculate_points_returns_default_when_diff_is_zero(strategy):
    _set_shared_values(strategy, user_avg=10, all_avg=5)
    strategy.user_points_service.get_last_window_time_diff.return_value = 5
    strategy.user_points_service.get_new_last_window_time_diff.return_value = 5

    points, status = await strategy.calculate_points("game_id", "task_id", "user_id")

    assert points == strategy.default_points_task_campaign
    assert status == "default"
