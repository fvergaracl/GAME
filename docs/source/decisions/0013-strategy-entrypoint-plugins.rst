======================================================
ADR 0013: External strategies via an entry-point group
======================================================

:Status: Accepted

Context
=======

Third parties should be able to ship their own strategies without forking the
engine.

Decision
========

``_load_external_strategies`` (``app/engine/strategy_registry.py``) reads the
``game.strategies`` entry-point group from installed package metadata and loads
each entry, which triggers its ``@register_strategy`` decorator. Loading is
lazy (on the first registry read) and guarded so it runs once. An entry point
that fails to import is isolated and logged, not fatal.

Consequences
============

* A clean plugin model: install a package and its strategies appear under their
  public ids, no fork required.
* External strategy code runs in-process and is trusted - unlike the sandboxed
  DSL (see :doc:`0007-dsl-sandbox`).
* Known gap: the entry-point load path is not currently exercised by a test, so
  changes there are not regression-guarded.

See also
========

* :doc:`/strategies` - "Extending the engine in code".
* :doc:`0006-stable-strategy-ids` - the registration mechanism plugins use.
