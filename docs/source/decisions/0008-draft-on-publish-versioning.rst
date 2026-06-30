==================================================
ADR 0008: Draft-on-publish versioning for the DSL
==================================================

:Status: Accepted

Context
=======

Editing a custom strategy that is live in production must not silently change
running behavior. Overwriting the stored definition would do exactly that.

Decision
========

``StrategyDefinitionService``
(``app/services/strategy_definition_service.py``) never overwrites a published
strategy. Create yields ``version=1`` / ``DRAFT``; editing a draft mutates it
in place; **editing a published row forks ``version+1`` as a new draft**,
leaving the published copy untouched. Publishing transitions the draft to
``PUBLISHED`` and archives the prior published sibling, so ``(realmId, name)``
has at most one live row (enforced by a unique constraint on
``(realmId, name, version)``). Only ``PUBLISHED`` definitions execute in
production; rollback restores a prior version.

Consequences
============

* Production keeps running the published version until an explicit publish;
  experimentation is free.
* Full, deterministic version history; rollback cascades the ``strategyId``
  change to every game and task that pointed at the archived version.
* Cost: more rows, and editors must understand draft vs. published.

See also
========

* :doc:`/strategies` - "The custom-strategy lifecycle" and versioning
  guarantees.
