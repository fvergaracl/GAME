import random
from types import SimpleNamespace

import numpy as np

from app.engine.greencrowdStrategy import (assign_random_scores,
                                           get_random_values_from_tasks)


def _records_for_random_range():
    return [
        SimpleNamespace(
            data={
                "tasks": [
                    {
                        "dimensions": [
                            {"DIM_BP": 2},
                            {"DIM_LBE": 4},
                            {"DIM_TD": 6},
                            {"DIM_PP": 8},
                            {"DIM_S": 10},
                        ]
                    }
                ]
            }
        )
    ]


def test_fixed_seed_produces_deterministic_random_values_from_tasks():
    records = _records_for_random_range()

    random.seed(2026)
    first = get_random_values_from_tasks(records)
    random.seed(2026)
    second = get_random_values_from_tasks(records)

    assert first == second


def test_fixed_seed_produces_deterministic_assign_random_scores():
    random.seed(99)
    first = assign_random_scores(1, 10)
    random.seed(99)
    second = assign_random_scores(1, 10)

    assert first == second


def test_multi_seed_distribution_for_assign_random_scores_is_stable_and_bounded():
    dimensions = ["DIM_BP", "DIM_TD", "DIM_LBE", "DIM_PP", "DIM_S"]
    samples = {dim: [] for dim in dimensions}

    for seed in range(200):
        random.seed(seed)
        result = assign_random_scores(1, 10)
        for dim in dimensions:
            samples[dim].append(result[dim])

    for dim in dimensions:
        values = np.array(samples[dim], dtype=float)
        assert values.min() >= 1
        assert values.max() <= 10
        assert 4.0 <= values.mean() <= 7.0
        assert 3.0 <= values.var() <= 15.0
