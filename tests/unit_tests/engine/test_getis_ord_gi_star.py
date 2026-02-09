import numpy as np
import pytest

from app.engine.getis_ord_gi_star import (GetisOrdStrategy, compute_getis_ord_gi_star,
                                          rank_hotspots)


def test_compute_getis_ord_requires_2d_grid():
    with pytest.raises(ValueError):
        compute_getis_ord_gi_star([1, 2, 3])


def test_compute_getis_ord_returns_zeros_for_single_cell_grid():
    grid = np.array([[5.0]])

    scores = compute_getis_ord_gi_star(grid)

    assert scores.shape == (1, 1)
    assert scores[0, 0] == 0.0


def test_compute_getis_ord_returns_zeros_when_variance_is_zero():
    grid = np.full((3, 3), 7.0)

    scores = compute_getis_ord_gi_star(grid)

    assert np.array_equal(scores, np.zeros((3, 3)))


def test_compute_getis_ord_detects_known_center_hotspot():
    grid = np.ones((5, 5), dtype=float)
    grid[2, 2] = 12.0

    scores = compute_getis_ord_gi_star(grid)

    top_cell = np.unravel_index(np.argmax(scores), scores.shape)
    hotspot_cluster = {(2, 2), (1, 2), (2, 1), (2, 3), (3, 2)}
    assert top_cell in hotspot_cluster
    assert scores[2, 2] > 0
    assert scores[2, 2] > scores[0, 0]


def test_compute_getis_ord_preserves_symmetry_for_symmetric_input():
    grid = np.array(
        [
            [1.0, 2.0, 2.0, 1.0],
            [2.0, 3.0, 3.0, 2.0],
            [2.0, 3.0, 3.0, 2.0],
            [1.0, 2.0, 2.0, 1.0],
        ]
    )

    scores = compute_getis_ord_gi_star(grid)

    assert np.allclose(scores, np.flipud(scores))
    assert np.allclose(scores, np.fliplr(scores))


def test_hotspot_ranking_is_stable_under_small_perturbation():
    base_grid = np.ones((5, 5), dtype=float)
    base_grid[2, 2] = 15.0
    perturbed_grid = base_grid.copy()
    perturbed_grid[1, 1] += 0.4

    base_rank = rank_hotspots(base_grid)
    perturbed_rank = rank_hotspots(perturbed_grid)

    base_top3 = {coord for coord, _ in base_rank[:3]}
    perturbed_top3 = {coord for coord, _ in perturbed_rank[:3]}

    hotspot_cluster = {(2, 2), (1, 2), (2, 1), (2, 3), (3, 2)}
    assert base_rank[0][0] in hotspot_cluster
    assert perturbed_rank[0][0] in hotspot_cluster
    assert len(base_top3 & perturbed_top3) >= 2


def test_rank_hotspots_sorts_by_score_descending():
    grid = np.array([[1.0, 1.0, 1.0], [1.0, 9.0, 1.0], [1.0, 1.0, 1.0]])

    ranked = rank_hotspots(grid)

    assert ranked[0][0] in {(1, 1), (0, 1), (1, 0), (1, 2), (2, 1)}
    assert ranked[0][1] >= ranked[-1][1]


@pytest.mark.asyncio
async def test_getis_ord_strategy_behaviour_and_metadata(capsys):
    strategy = GetisOrdStrategy()

    assert strategy.get_strategy_name() == "GeoEquityGamificationModel"
    assert strategy.get_strategy_name_slug() == "geo_equity_gamification_model"
    assert strategy.get_variable_basic_points() == 10
    assert strategy.get_variable_bonus_points() == 10
    assert strategy.get_strategy_id() == "GetisOrdStrategy"
    assert isinstance(strategy.hash_version, str)
    assert len(strategy.hash_version) == 64

    changed = strategy.set_variables({"variable_basic_points": 15, "unknown": 1})
    assert changed == ["variable_basic_points"]
    assert strategy.get_variable("variable_basic_points") == 15
    assert strategy.set_variable("variable_bonus_points", 17) is True
    assert strategy.set_variable("not_present", 1) is False
    assert strategy.get_variable("not_present") is None

    metadata = strategy.get_strategy()
    assert metadata["name"] == "GeoEquityGamificationModel"
    assert metadata["variables"]["variable_basic_points"] == 15
    assert metadata["variables"]["variable_bonus_points"] == 17

    points = await strategy.calculate_points()
    assert points == 15
    assert strategy.simulate_strategy() is None

    dot = strategy.generate_logic_graph(format="svg")
    assert dot.format == "svg"
    assert "No logic graph available" in dot.source

    strategy.debug = True
    strategy.debug_print("debug-line")
    captured = capsys.readouterr()
    assert "debug-line" in captured.out
