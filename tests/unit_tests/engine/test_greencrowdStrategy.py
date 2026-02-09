import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import InternalServerError
from app.engine.greencrowdStrategy import (GREENCROWDGamificationStrategy,
                                           assign_random_scores,
                                           get_average_values_from_tasks,
                                           get_dynamic_values_from_tasks,
                                           get_random_values_from_tasks)
from app.schema.task_schema import SimulatedTaskPoints


class QueryRecords:
    def __init__(self, records):
        self._records = records

    def all(self):
        return self._records


def _build_sim_task_dict(
    external_task_id,
    dim_bp=1,
    dim_lbe=2,
    dim_td=3,
    dim_pp=4,
    dim_s=5,
    external_user_id="user-1",
    user_group="random_range",
    expiration_date=None,
):
    if expiration_date is None:
        expiration_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=10
        )
    return {
        "externalUserId": external_user_id,
        "externalTaskId": external_task_id,
        "userGroup": user_group,
        "dimensions": [
            {"DIM_BP": dim_bp},
            {"DIM_LBE": dim_lbe},
            {"DIM_TD": dim_td},
            {"DIM_PP": dim_pp},
            {"DIM_S": dim_s},
        ],
        "totalSimulatedPoints": dim_bp + dim_lbe + dim_td + dim_pp + dim_s,
        "expirationDate": expiration_date.strftime("%Y-%m-%d %H:%M:%S.%f%z"),
    }


def _build_strategy_with_mocked_container():
    task_service = MagicMock()
    game_service = MagicMock()
    user_points_service = MagicMock()
    user_service = MagicMock()
    logs_service = MagicMock()
    with patch(
        "app.engine.greencrowdStrategy.Container.task_service",
        new=MagicMock(return_value=task_service),
    ), patch(
        "app.engine.greencrowdStrategy.Container.game_service",
        new=MagicMock(return_value=game_service),
    ), patch(
        "app.engine.greencrowdStrategy.Container.user_points_service",
        new=MagicMock(return_value=user_points_service),
    ), patch(
        "app.engine.greencrowdStrategy.Container.user_service",
        new=MagicMock(return_value=user_service),
    ), patch(
        "app.engine.greencrowdStrategy.Container.logs_service",
        new=MagicMock(return_value=logs_service),
    ), patch.object(
        __import__("app.engine.greencrowdStrategy", fromlist=["configs"]).configs,
        "SECRET_KEY",
        "test-secret",
    ):
        strategy = GREENCROWDGamificationStrategy()
    return strategy


def test_get_random_values_from_tasks_uses_callback_data():
    records = [
        SimpleNamespace(
            data={
                "tasks": [{"dimensions": [{"DIM_BP": 99}]}],
                "callbackData": [
                    {
                        "dimensions": [
                            {"DIM_BP": 1},
                            {"DIM_LBE": 2},
                            {"DIM_TD": 3},
                            {"DIM_PP": 4},
                            {"DIM_S": 5},
                        ]
                    }
                ],
            }
        )
    ]

    with patch("app.engine.greencrowdStrategy.random.randint", side_effect=[1, 2, 3, 4, 5]):
        result = get_random_values_from_tasks(records)

    assert result == {"DIM_BP": 1, "DIM_LBE": 2, "DIM_TD": 3, "DIM_PP": 4, "DIM_S": 5}


def test_get_random_values_from_tasks_with_empty_records_uses_default_range():
    with patch("app.engine.greencrowdStrategy.random.randint", side_effect=lambda a, b: a + b):
        result = get_random_values_from_tasks([])

    assert result == {
        "DIM_BP": 10,
        "DIM_LBE": 10,
        "DIM_TD": 10,
        "DIM_PP": 10,
        "DIM_S": 10,
    }


def test_get_average_values_from_tasks_uses_callback_data_and_fallback():
    records = [
        SimpleNamespace(
            data={
                "tasks": [],
                "callbackData": [
                    {"dimensions": [{"DIM_BP": 2}]},
                    {"dimensions": [{"DIM_BP": 4}]},
                ],
            }
        )
    ]

    result = get_average_values_from_tasks(SimpleNamespace(), records)

    assert result["DIM_BP"] == 3
    assert result["DIM_LBE"] == 5
    assert result["DIM_TD"] == 5
    assert result["DIM_PP"] == 5
    assert result["DIM_S"] == 5


def test_get_dynamic_values_from_tasks_returns_zero_when_external_task_id_invalid():
    task = SimpleNamespace(id="task-1", externalTaskId="invalid")
    result = get_dynamic_values_from_tasks(
        task=task,
        list_ids_tasks=[],
        all_records=QueryRecords([]),
        user=SimpleNamespace(id="user-1"),
        variable_basic_points=10,
        variable_lbe_multiplier=0.5,
    )

    assert result == {"DIM_BP": 0, "DIM_LBE": 0, "DIM_TD": 0, "DIM_PP": 0, "DIM_S": 0}


def test_get_dynamic_values_from_tasks_calculates_dimensions_and_handles_bad_task_in_list():
    now_utc = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    task = SimpleNamespace(id="task-a", externalTaskId="poi_1")
    user = SimpleNamespace(id="user-1")
    records = [
        SimpleNamespace(taskId="task-a", userId="user-1", created_at=now_utc - datetime.timedelta(hours=8)),
        SimpleNamespace(taskId="task-a", userId="user-1", created_at=now_utc - datetime.timedelta(hours=4)),
        SimpleNamespace(taskId="task-b", userId="user-2", created_at=now_utc - datetime.timedelta(hours=1)),
    ]

    result = get_dynamic_values_from_tasks(
        task=task,
        list_ids_tasks=[
            {"id": "task-a", "externalTaskId": "poi_1"},
            {"id": "task-b", "externalTaskId": "bad-task-id"},
        ],
        all_records=QueryRecords(records),
        user=user,
        variable_basic_points=10,
        variable_lbe_multiplier=0.5,
    )

    assert set(result.keys()) == {"DIM_BP", "DIM_LBE", "DIM_TD", "DIM_PP", "DIM_S"}
    assert all(isinstance(v, int) for v in result.values())


def test_assign_random_scores_returns_all_dimensions():
    with patch("app.engine.greencrowdStrategy.random.randint", side_effect=[3, 4, 5, 6, 7]):
        result = assign_random_scores(1, 10)

    assert result == {"DIM_BP": 3, "DIM_TD": 4, "DIM_LBE": 5, "DIM_PP": 6, "DIM_S": 7}


def test_strategy_init_generate_logic_graph_and_hash():
    strategy = _build_strategy_with_mocked_container()

    assert strategy.variable_basic_points == 10
    assert strategy.variable_lbe_multiplier == 0.5
    assert strategy.variable_simulation_valid_until == 15
    assert strategy.task_service is not None
    assert strategy.game_service is not None
    assert strategy.user_points_service is not None
    assert strategy.user_service is not None
    assert strategy.service_log is not None

    dot = strategy.generate_logic_graph(format="svg")
    assert dot.format == "svg"
    assert "checkLBE" in dot.source
    assert "assignStreak" in dot.source

    hash_1 = strategy.generate_hash({"a": 1})
    hash_2 = strategy.generate_hash({"a": 1})
    hash_3 = strategy.generate_hash({"a": 2})
    assert hash_1 == hash_2
    assert hash_1 != hash_3


def test_simulate_strategy_returns_internal_server_error_on_missing_data():
    strategy = _build_strategy_with_mocked_container()
    result = strategy.simulate_strategy(data_to_simulate={})

    assert isinstance(result, InternalServerError)


def test_simulate_strategy_returns_zero_points_when_last_task_is_old():
    strategy = _build_strategy_with_mocked_container()
    task = SimpleNamespace(id="task-1", externalTaskId="poi_1")
    old_point = SimpleNamespace(
        taskId="task-1",
        created_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=400),
    )

    result = strategy.simulate_strategy(
        data_to_simulate={
            "task": task,
            "allTasks": [task],
            "externalUserId": "user-1",
        },
        user_last_task=old_point,
    )

    assert isinstance(result, SimulatedTaskPoints)
    assert result.totalSimulatedPoints == 0


def test_simulate_strategy_random_range_branch():
    strategy = _build_strategy_with_mocked_container()
    task = SimpleNamespace(id="task-1", externalTaskId="poi_1")
    strategy.user_points_service.get_all_point_of_tasks_list.return_value = [
        SimpleNamespace(
            data={
                "tasks": [
                    {
                        "dimensions": [
                            {"DIM_BP": 1},
                            {"DIM_LBE": 1},
                            {"DIM_TD": 1},
                            {"DIM_PP": 1},
                            {"DIM_S": 1},
                        ]
                    }
                ]
            }
        )
    ]

    with patch("app.engine.greencrowdStrategy.random.randint", side_effect=[1, 2, 3, 4, 5]):
        result = strategy.simulate_strategy(
            data_to_simulate={
                "task": task,
                "allTasks": [task],
                "externalUserId": "user-1",
            },
            userGroup="random_range",
        )

    assert isinstance(result, SimulatedTaskPoints)
    assert result.totalSimulatedPoints == 15


def test_simulate_strategy_average_score_branch():
    strategy = _build_strategy_with_mocked_container()
    task = SimpleNamespace(id="task-1", externalTaskId="poi_1")
    strategy.user_points_service.get_all_point_of_tasks_list.return_value = [
        SimpleNamespace(
            data={
                "tasks": [],
                "callbackData": [
                    {
                        "dimensions": [
                            {"DIM_BP": 2},
                            {"DIM_LBE": 4},
                            {"DIM_TD": 6},
                            {"DIM_PP": 8},
                            {"DIM_S": 10},
                        ]
                    }
                ],
            }
        )
    ]

    result = strategy.simulate_strategy(
        data_to_simulate={
            "task": task,
            "allTasks": [task],
            "externalUserId": "user-1",
        },
        userGroup="average_score",
    )

    assert isinstance(result, SimulatedTaskPoints)
    assert result.totalSimulatedPoints == 30


def test_simulate_strategy_dynamic_calculation_branch():
    strategy = _build_strategy_with_mocked_container()
    now_utc = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    task = SimpleNamespace(id="task-1", externalTaskId="poi_1")
    strategy.user_points_service.get_all_point_of_tasks_list.return_value = QueryRecords(
        [
            SimpleNamespace(taskId="task-1", userId="user-1", created_at=now_utc - datetime.timedelta(hours=6)),
            SimpleNamespace(taskId="task-1", userId="user-1", created_at=now_utc - datetime.timedelta(hours=3)),
            SimpleNamespace(taskId="task-2", userId="user-2", created_at=now_utc - datetime.timedelta(hours=1)),
        ]
    )
    strategy.user_service.get_user_by_externalUserId.return_value = SimpleNamespace(id="user-1")
    second_task = SimpleNamespace(id="task-2", externalTaskId="poi_2")

    result = strategy.simulate_strategy(
        data_to_simulate={
            "task": task,
            "allTasks": [task, second_task],
            "externalUserId": "user-1",
        },
        userGroup="dynamic_calculation",
    )

    assert isinstance(result, SimulatedTaskPoints)
    assert result.userGroup == "dynamic_calculation"
    assert isinstance(result.totalSimulatedPoints, int)


def test_check_is_expired():
    strategy = _build_strategy_with_mocked_container()
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=1)

    assert strategy.checkISExpired(past) is True
    assert strategy.checkISExpired(future) is False


@pytest.mark.asyncio
async def test_calculate_points_returns_invalid_hash_when_not_was_calculated():
    strategy = _build_strategy_with_mocked_container()
    data = {
        "simulationHash": "expected-hash",
        "tasks": [_build_sim_task_dict("poi_1")],
    }

    with patch(
        "app.engine.greencrowdStrategy.calculate_hash_simulated_strategy",
        return_value="other-hash",
    ):
        result = await strategy.calculate_points("game-1", "poi_1", "user-1", data)

    assert result == (-1, "Invalid hash")


@pytest.mark.asyncio
async def test_calculate_points_with_empty_tasks_generates_valid_simulation():
    strategy = _build_strategy_with_mocked_container()
    simulated_task = SimulatedTaskPoints(**_build_sim_task_dict("poi_1"))
    strategy.game_service.get_game_by_external_id.return_value = SimpleNamespace(id=str(uuid4()))
    strategy.user_points_service.get_points_simulated_of_user_in_game = AsyncMock(
        return_value=([simulated_task], "game-1")
    )
    strategy.user_points_service.get_points_of_simulated_task.return_value = []
    data = {"tasks": [], "simulationHash": ""}

    with patch(
        "app.engine.greencrowdStrategy.calculate_hash_simulated_strategy",
        side_effect=["hash-initial", "hash-later"],
    ):
        points, case_name, callback_data = await strategy.calculate_points(
            "game-1", "poi_1", "user-1", data
        )

    assert points == 15
    assert case_name == "Valid Simulation"
    assert callback_data is None


@pytest.mark.asyncio
async def test_calculate_points_uses_previous_points_branch():
    strategy = _build_strategy_with_mocked_container()
    original_task = _build_sim_task_dict("poi_1")
    resimulated_task = SimulatedTaskPoints(
        **_build_sim_task_dict("poi_1", dim_bp=2, dim_lbe=2, dim_td=2, dim_pp=2, dim_s=2)
    )
    strategy.user_points_service.get_points_of_simulated_task.return_value = [SimpleNamespace(id=1)]
    strategy.game_service.get_game_by_external_id.return_value = SimpleNamespace(id=str(uuid4()))
    strategy.user_points_service.get_points_simulated_of_user_in_game = AsyncMock(
        return_value=([resimulated_task], "game-1")
    )

    with patch(
        "app.engine.greencrowdStrategy.calculate_hash_simulated_strategy",
        side_effect=["valid-hash", "new-hash"],
    ), patch("app.engine.greencrowdStrategy.add_log", new=AsyncMock()):
        points, case_name, callback_data = await strategy.calculate_points(
            "game-1",
            "poi_1",
            "user-1",
            {"tasks": [original_task], "simulationHash": "valid-hash"},
        )

    assert points == 10
    assert case_name == "Valid Simulation - Origin: Used simulation"
    assert callback_data == [resimulated_task]


@pytest.mark.asyncio
async def test_calculate_points_handles_expired_simulation():
    strategy = _build_strategy_with_mocked_container()
    expired = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    original_task = _build_sim_task_dict("poi_1", expiration_date=expired)
    renewed_task = SimulatedTaskPoints(
        **_build_sim_task_dict("poi_1", dim_bp=3, dim_lbe=3, dim_td=3, dim_pp=3, dim_s=3)
    )
    strategy.user_points_service.get_points_of_simulated_task.return_value = []
    strategy.game_service.get_game_by_external_id.return_value = SimpleNamespace(id=str(uuid4()))
    strategy.user_points_service.get_points_simulated_of_user_in_game = AsyncMock(
        return_value=([renewed_task], "game-1")
    )

    with patch(
        "app.engine.greencrowdStrategy.calculate_hash_simulated_strategy",
        side_effect=["valid-hash", "renewed-hash"],
    ):
        points, case_name, callback_data = await strategy.calculate_points(
            "game-1",
            "poi_1",
            "user-1",
            {"tasks": [original_task], "simulationHash": "valid-hash"},
        )

    assert points == 15
    assert case_name == "Valid Simulation - Origin: Expired simulation"
    assert callback_data == [renewed_task]
