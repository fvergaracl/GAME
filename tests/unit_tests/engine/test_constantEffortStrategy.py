# tests/test_constant_effort_strategy.py
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.engine.constantEffortStrategy import ConstantEffortStrategy


@pytest.fixture
def strategy():
    strategy = ConstantEffortStrategy()
    strategy.task_service = MagicMock()
    strategy.user_points_service = MagicMock()
    return strategy


@pytest.mark.asyncio
async def test_calculate_points_default(strategy):
    strategy.user_points_service.get_user_task_measurements_count_the_last_seconds.return_value = (
        0
    )

    points, reward_type = await strategy.calculate_points(
        "game_id", "task_id", "user_id"
    )

    assert points == 1
    assert reward_type == "BasicReward"


@pytest.mark.asyncio
async def test_calculate_points_consistent_effort(strategy):
    strategy.user_points_service.get_user_task_measurements_count_the_last_seconds.return_value = (
        4
    )

    points, reward_type = await strategy.calculate_points(
        "game_id", "task_id", "user_id"
    )

    assert points > 1
    assert reward_type == "ConstantEffortReward"


@pytest.mark.asyncio
async def test_calculate_points_no_measurements(strategy):
    strategy.user_points_service.get_user_task_measurements_count_the_last_seconds.return_value = (
        0
    )

    points, reward_type = await strategy.calculate_points(
        "game_id", "task_id", "user_id"
    )

    assert points == 1
    assert reward_type == "BasicReward"


def test_calculate_points_from_consistency(strategy):
    effort_interval = strategy.get_variable("variable_constant_effort_interval_minutes")
    if effort_interval == 100:
        points = strategy._calculate_points_from_consistency(100)
        assert points == 100
    points = strategy._calculate_points_from_consistency(50)
    assert points == 50

    points = strategy._calculate_points_from_consistency(0)
    assert points == 1


def test_debug_print(strategy, capsys):
    strategy.debug = True
    strategy.debug_print("Test message")

    captured = capsys.readouterr()
    assert "Test message" in captured.out
