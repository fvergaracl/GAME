"""Explicit strategy registry.

Replaces the legacy filesystem-scan in
:mod:`app.engine.all_engine_strategies`. Strategy classes opt-in by
decorating themselves with :func:`register_strategy`. External packages
can contribute strategies via the ``game.strategies`` entry-point group
declared in their packaging metadata.
"""

from __future__ import annotations

import logging
from importlib import metadata
from typing import Callable, TypeVar

_log = logging.getLogger(__name__)

T = TypeVar("T", bound=type)

_REGISTRY: dict[str, type] = {}
_external_loaded: bool = False


def register_strategy(id: str, *, version: str | None = None) -> Callable[[T], T]:
    """Register a strategy class under a stable, public id.

    The id is the value persisted on games and returned by the API, so it must
    remain stable across class renames or file moves.

    Args:
        id: Public identifier for the strategy (e.g. ``"default"``).
        version: Optional version string. When provided, it is also exposed as
            the ``__strategy_version__`` class attribute.

    Raises:
        ValueError: If ``id`` is empty or another class is already registered
            under the same id.
    """

    if not id or not isinstance(id, str):
        raise ValueError("Strategy id must be a non-empty string")

    def decorator(cls: T) -> T:
        existing = _REGISTRY.get(id)
        if existing is not None and existing is not cls:
            raise ValueError(
                f"Strategy id {id!r} already registered by "
                f"{existing.__module__}.{existing.__name__}"
            )
        cls.__strategy_id__ = id
        if version is not None:
            cls.__strategy_version__ = version
        _REGISTRY[id] = cls
        return cls

    return decorator


def _load_external_strategies() -> None:
    """Import third-party strategies via the ``game.strategies`` entry point.

    Each entry point should resolve to a strategy class (or to its module);
    importing it triggers the :func:`register_strategy` decorator.
    """
    global _external_loaded
    if _external_loaded:
        return
    _external_loaded = True
    try:
        eps = metadata.entry_points(group="game.strategies")
    except TypeError:
        eps = metadata.entry_points().get("game.strategies", [])
    for ep in eps:
        try:
            ep.load()
        except Exception as exc:
            _log.warning("Failed loading strategy entry point %s: %s", ep, exc)


def registered_strategies() -> dict[str, type]:
    """Return a snapshot of the registry as ``{id: class}``."""
    _load_external_strategies()
    return dict(_REGISTRY)


def get_registered_class(strategy_id: str) -> type | None:
    """Lookup a registered strategy class by id, or ``None`` if missing."""
    _load_external_strategies()
    return _REGISTRY.get(strategy_id)


def clear_registry() -> None:
    """Reset the registry. Intended for tests only."""
    global _external_loaded
    _REGISTRY.clear()
    _external_loaded = False
