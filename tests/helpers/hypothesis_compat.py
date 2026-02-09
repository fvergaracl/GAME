"""
Minimal fallback utilities for property-style tests when Hypothesis is not installed.

If real Hypothesis is available, tests should import from it directly and this
module will be unused.
"""

from __future__ import annotations

import functools
import inspect
import random
from dataclasses import dataclass


@dataclass
class _Strategy:
    draw_fn: callable

    def draw(self, rnd: random.Random):
        return self.draw_fn(rnd)


class strategies:
    @staticmethod
    def integers(min_value: int = 0, max_value: int = 100) -> _Strategy:
        return _Strategy(lambda rnd: rnd.randint(min_value, max_value))

    @staticmethod
    def floats(min_value: float = 0.0, max_value: float = 1.0) -> _Strategy:
        return _Strategy(lambda rnd: rnd.uniform(min_value, max_value))

    @staticmethod
    def sampled_from(values) -> _Strategy:
        values = list(values)
        return _Strategy(lambda rnd: rnd.choice(values))

    @staticmethod
    def just(value) -> _Strategy:
        return _Strategy(lambda rnd: value)

    @staticmethod
    def lists(
        element_strategy: _Strategy,
        min_size: int = 0,
        max_size: int = 10,
    ) -> _Strategy:
        return _Strategy(
            lambda rnd: [
                element_strategy.draw(rnd)
                for _ in range(rnd.randint(min_size, max_size))
            ]
        )


def settings(max_examples: int = 25, **_kwargs):
    def decorator(func):
        setattr(func, "_fallback_max_examples", max_examples)
        return func

    return decorator


def given(*given_args, **given_kwargs):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            max_examples = getattr(func, "_fallback_max_examples", 25)
            rnd = random.Random(0)
            for _ in range(max_examples):
                generated_args = [
                    strategy.draw(rnd) if hasattr(strategy, "draw") else strategy
                    for strategy in given_args
                ]
                generated_kwargs = {
                    key: strategy.draw(rnd) if hasattr(strategy, "draw") else strategy
                    for key, strategy in given_kwargs.items()
                }
                func(*args, *generated_args, **kwargs, **generated_kwargs)

        # Prevent pytest from treating generated parameters as fixtures.
        wrapper.__signature__ = inspect.Signature()
        return wrapper

    return decorator
