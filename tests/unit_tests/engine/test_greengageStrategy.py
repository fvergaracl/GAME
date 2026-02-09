from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.engine.greengageStrategy import GREENGAGEGamificationStrategy


@pytest.fixture
def strategy_bundle():
    task_service = MagicMock()
    user_points_service = MagicMock()
    with patch(
        "app.engine.greengageStrategy.Container.task_service",
        new=MagicMock(return_value=task_service),
    ), patch(
        "app.engine.greengageStrategy.Container.user_points_service",
        new=MagicMock(return_value=user_points_service),
    ):
        strategy = GREENGAGEGamificationStrategy()
    strategy.debug = False
    return strategy, task_service, user_points_service


def test_init_sets_expected_configuration(strategy_bundle):
    strategy, task_service, user_points_service = strategy_bundle

    assert strategy.strategy_name == "GREENGAGEGamificationStrategy"
    assert strategy.strategy_name_slug == "greengage_gamification"
    assert strategy.strategy_version == "0.0.1"
    assert strategy.task_service is task_service
    assert strategy.user_points_service is user_points_service
    assert strategy.variable_default_points == 10
    assert strategy.variable_minutes_to_check == 1
    assert strategy.time_ranges == [0, 1, 15, 30, 60, float("inf")]
    assert strategy.variable_complexity["Very_high"] == 100
    assert strategy.variable_dimension_complexity == {
        "development": 0,
        "exploitation": 0,
        "management": 0,
    }
    assert not hasattr(strategy, "variable_basic_points")
    assert not hasattr(strategy, "variable_bonus_points")


def test_get_dpte_uses_floor_time_range_and_fallback(strategy_bundle):
    strategy, _, _ = strategy_bundle

    assert strategy.get_DPTE(points=3, minutes=0) == 0
    assert strategy.get_DPTE(points=2, minutes=16) == 30
    assert strategy.get_DPTE(points=2, minutes=float("inf")) == 120


def test_get_bp_and_get_pbp_apply_expected_multipliers(strategy_bundle):
    strategy, _, _ = strategy_bundle

    assert strategy.get_BP(points=10, minutes=16) == 225
    assert strategy.get_PBP(points=10, minutes=16) == 187.5


def test_generate_logic_graph_contains_expected_nodes_and_edges(strategy_bundle):
    strategy, _, _ = strategy_bundle

    dot = strategy.generate_logic_graph(format="svg")

    assert dot.format == "svg"
    assert "checkif0" in dot.source
    assert "Case 4.2 (DPTE)" in dot.source
    assert "checkif2records -> checkififTimeIsGreaterThanGlobalAVG" in dot.source


@pytest.mark.asyncio
async def test_calculate_points_requires_minutes_field(strategy_bundle):
    strategy, _, _ = strategy_bundle

    result = await strategy.calculate_points("game-1", "task-1", "user-1", data={})

    assert result == (-1, 'The "minutes" field is required into the data')


@pytest.mark.asyncio
async def test_calculate_points_rejects_non_integer_minutes(strategy_bundle):
    strategy, _, _ = strategy_bundle

    result = await strategy.calculate_points(
        "game-1", "task-1", "user-1", data={"minutes": "5"}
    )

    assert result == (-1, "The minutes must be a number equal or greater than 0")


@pytest.mark.asyncio
async def test_calculate_points_case_1_1_and_maps_task_params(strategy_bundle):
    strategy, task_service, user_points_service = strategy_bundle
    task_service.get_task_params_by_externalTaskId.return_value = [
        SimpleNamespace(key="development", value=10),
        SimpleNamespace(key="exploitation", value=20),
        SimpleNamespace(key="management", value=30),
        SimpleNamespace(key="ignored", value=99),
    ]
    user_points_service.user_has_record_before_in_externalTaskId_last_min.return_value = (
        False
    )

    result = await strategy.calculate_points(
        "game-1", "task-1", "user-1", data={"minutes": 0}
    )

    assert result == (10, "Case 1.1 (DP)")
    assert strategy.variable_dimension_complexity == {
        "development": 10,
        "exploitation": 20,
        "management": 30,
    }
    user_points_service.count_personal_records_by_external_game_id.assert_not_called()


@pytest.mark.asyncio
async def test_calculate_points_case_1_2_when_user_has_previous_recent_record(
    strategy_bundle,
):
    strategy, task_service, user_points_service = strategy_bundle
    task_service.get_task_params_by_externalTaskId.return_value = []
    user_points_service.user_has_record_before_in_externalTaskId_last_min.return_value = (
        True
    )

    result = await strategy.calculate_points(
        "game-1", "task-1", "user-1", data={"minutes": 0}
    )

    assert result == (5.0, "Case 1.2 (DP/2)")


@pytest.mark.asyncio
async def test_calculate_points_case_2_when_personal_records_are_less_than_two(
    strategy_bundle,
):
    strategy, task_service, user_points_service = strategy_bundle
    task_service.get_task_params_by_externalTaskId.return_value = None
    strategy.variable_dimension_complexity = {
        "development": 99,
        "exploitation": 99,
        "management": 99,
    }
    user_points_service.user_has_record_before_in_externalTaskId_last_min.return_value = (
        False
    )
    user_points_service.count_personal_records_by_external_game_id.return_value = 1

    result = await strategy.calculate_points(
        "game-1", "task-1", "user-1", data={"minutes": 5}
    )

    assert result == (20, "Case 2 (DP x 2)")
    assert strategy.variable_dimension_complexity == {
        "development": 0,
        "exploitation": 0,
        "management": 0,
    }


@pytest.mark.asyncio
async def test_calculate_points_case_3_when_minutes_are_above_global_average(
    strategy_bundle,
):
    strategy, task_service, user_points_service = strategy_bundle
    task_service.get_task_params_by_externalTaskId.return_value = []
    user_points_service.user_has_record_before_in_externalTaskId_last_min.return_value = (
        False
    )
    user_points_service.count_personal_records_by_external_game_id.return_value = 2
    user_points_service.get_global_avg_by_external_game_id.return_value = 10

    result = await strategy.calculate_points(
        "game-1", "task-1", "user-1", data={"minutes": 11}
    )

    assert result == (15.0, "Case 3 (BP)")
    user_points_service.get_personal_avg_by_external_game_id.assert_not_called()


@pytest.mark.asyncio
async def test_calculate_points_case_4_1_when_minutes_are_above_personal_average(
    strategy_bundle,
):
    strategy, task_service, user_points_service = strategy_bundle
    task_service.get_task_params_by_externalTaskId.return_value = []
    user_points_service.user_has_record_before_in_externalTaskId_last_min.return_value = (
        False
    )
    user_points_service.count_personal_records_by_external_game_id.return_value = 2
    user_points_service.get_global_avg_by_external_game_id.return_value = 20
    user_points_service.get_personal_avg_by_external_game_id.return_value = 15

    result = await strategy.calculate_points(
        "game-1", "task-1", "user-1", data={"minutes": 16}
    )

    assert result == (187.5, "Case 4.1 (PBP)")


@pytest.mark.asyncio
async def test_calculate_points_case_4_2_when_minutes_are_not_above_personal_average(
    strategy_bundle,
):
    strategy, task_service, user_points_service = strategy_bundle
    task_service.get_task_params_by_externalTaskId.return_value = []
    user_points_service.user_has_record_before_in_externalTaskId_last_min.return_value = (
        False
    )
    user_points_service.count_personal_records_by_external_game_id.return_value = 2
    user_points_service.get_global_avg_by_external_game_id.return_value = 20
    user_points_service.get_personal_avg_by_external_game_id.return_value = 16

    result = await strategy.calculate_points(
        "game-1", "task-1", "user-1", data={"minutes": 16}
    )

    assert result == (150, "Case 4.2 (DPTE)")
