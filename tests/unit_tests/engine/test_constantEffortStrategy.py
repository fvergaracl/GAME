# tests/test_constant_effort_strategy.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from app.engine.constantEffortStrategy import ConstantEffortStrategy


@pytest.fixture
def strategy():
    strategy = ConstantEffortStrategy()
    strategy.task_service = MagicMock()
    strategy.user_points_service = MagicMock()
    return strategy


def test_calculate_points_default(strategy):
    strategy.user_points_service.get_user_task_measurements.return_value = []

    points, reward_type = strategy.calculate_points(
        "game_id", "task_id", "user_id")

    assert points == 1
    assert reward_type == "default"


def test_calculate_points_consistent_effort(strategy):
    now = datetime.now()
    measurements = [
        {"timestamp": now - timedelta(minutes=10)},
        {"timestamp": now - timedelta(minutes=8)},
        {"timestamp": now - timedelta(minutes=5)},
        {"timestamp": now - timedelta(minutes=2)}
    ]
    strategy.user_points_service.get_user_task_measurements.return_value = measurements

    points, reward_type = strategy.calculate_points(
        "game_id", "task_id", "user_id")

    assert points > 1
    assert reward_type == "ConstantEffortReward"


def test_calculate_points_no_measurements(strategy):
    strategy.user_points_service.get_user_task_measurements.return_value = []

    points, reward_type = strategy.calculate_points(
        "game_id", "task_id", "user_id")

    assert points == 1
    assert reward_type == "default"


def test_calculate_consistent_effort(strategy):
    now = datetime.now()
    measurements = [
        {"timestamp": now - timedelta(minutes=6)},
        {"timestamp": now - timedelta(minutes=4)},
        {"timestamp": now - timedelta(minutes=3)},
        {"timestamp": now}
    ]
    consistent_effort_count = strategy._calculate_consistent_effort(
        measurements)

    assert consistent_effort_count == 3


def test_calculate_points_from_consistency(strategy):
    points = strategy._calculate_points_from_consistency(50)

    assert points == 50


def test_debug_print(strategy, capsys):
    strategy.debug = True
    strategy.debug_print("Test message")

    captured = capsys.readouterr()
    assert "Test message" in captured.out
