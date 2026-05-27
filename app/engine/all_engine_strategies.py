"""Strategy enumeration backed by the explicit registry.

The legacy implementation walked ``app/engine`` with :func:`os.listdir`
(CWD-dependent), imported every module, picked classes by "first letter
uppercase", and mutated the list while iterating. It also could not load
strategies from external packages.

This module now:

1. Auto-discovers every module inside the :mod:`app.engine` package using
   :func:`pkgutil.iter_modules` against the package's resolved ``__path__``
   (independent of the current working directory), so newly added strategy
   files are picked up without editing this file.
2. Imports each module, which triggers ``@register_strategy`` and registers
   the class in :mod:`app.engine.strategy_registry`. Modules that don't
   register anything (helpers, base classes) simply contribute nothing.
3. Returns instances of every class currently in the registry. Third-party
   strategies declared via the ``game.strategies`` entry point are loaded
   lazily by the registry.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil

from app.engine.check_base_strategy_class import (
    check_class_methods_and_variables,
)
from app.engine.strategy_registry import registered_strategies

_log = logging.getLogger(__name__)

_PACKAGE_NAME = "app.engine"

# Modules in app.engine that are infrastructure, not strategies. They are
# imported as a side-effect of normal usage; we skip them during discovery
# to avoid pointless re-imports and to make the scan auditable.
_DISCOVERY_SKIP: frozenset[str] = frozenset(
    {
        "base_strategy",
        "check_base_strategy_class",
        "strategy_registry",
        "all_engine_strategies",
    }
)

_discovery_done = False


def _discover_strategy_modules() -> None:
    """Import every strategy module in :mod:`app.engine`.

    Discovery is safe-by-construction:

    * Uses the package's own ``__path__`` (not a CWD-relative string), so it
      works regardless of where the process was launched from.
    * Restricted to direct children of :mod:`app.engine`; we don't walk into
      arbitrary subpackages.
    * Skips private modules (leading underscore) and the infrastructure
      modules listed in :data:`_DISCOVERY_SKIP`.
    * Import errors are logged and isolated: one broken strategy file cannot
      take down the whole engine.
    """
    global _discovery_done
    if _discovery_done:
        return
    _discovery_done = True

    package = importlib.import_module(_PACKAGE_NAME)
    package_path = getattr(package, "__path__", None)
    if package_path is None:
        _log.error(
            "Package %s has no __path__; skipping discovery", _PACKAGE_NAME
        )
        return

    for module_info in pkgutil.iter_modules(package_path):
        name = module_info.name
        if module_info.ispkg:
            continue
        if name.startswith("_"):
            continue
        if name in _DISCOVERY_SKIP:
            continue
        full_name = f"{_PACKAGE_NAME}.{name}"
        try:
            importlib.import_module(full_name)
        except Exception as exc:
            _log.error(
                "Failed importing strategy module %s: %s", full_name, exc
            )


def all_engine_strategies() -> list:
    """Return instances of every registered, validated strategy class.

    Each instance has an ``id`` attribute set to the registered strategy
    id (the public identifier persisted on games and exposed by the API).

    :return: List of strategy instances, one per registered class. Classes
        that fail :func:`check_class_methods_and_variables` are skipped.
    :rtype: list
    """
    _discover_strategy_modules()

    instances: list = []
    for strategy_id, cls in registered_strategies().items():
        if not check_class_methods_and_variables(cls):
            _log.warning(
                "Strategy %s (%s) failed validation; skipping",
                strategy_id,
                cls.__name__,
            )
            continue
        instance = cls()
        instance.id = strategy_id
        instances.append(instance)
    return instances
