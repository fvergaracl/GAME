==========================================
ADR 0006: Stable public strategy ids
==========================================

:Status: Accepted

Context
=======

Strategy ids are persisted on ``Games.strategyId`` / ``Tasks.strategyId`` and
returned by the API. Tying them to Python class names would break stored data
on any class rename or file move. An earlier version discovered strategies by
scanning the filesystem and picking classes by a naming convention, which was
brittle and working-directory dependent.

Decision
========

Strategy classes opt in by decorating with
``@register_strategy(id=..., version=...)``
(``app/engine/strategy_registry.py``). The decorator stamps a
``__strategy_id__`` and registers the class under that **public id**, which is
documented to remain stable across class renames or file moves. Discovery is
now CWD-independent via ``pkgutil.iter_modules`` over ``app/engine``
(``app/engine/all_engine_strategies.py``).

Consequences
============

* Class and file renames are safe; stored ``strategyId`` values keep resolving.
* Registering two strategies under the same id fails loudly at import.
* Strategy code is trusted (in-process), unlike the sandboxed DSL.

See also
========

* :doc:`/strategies` - "Built-in strategies" and the stable-id guarantee.
* :doc:`0013-strategy-entrypoint-plugins` - how third parties register ids.
