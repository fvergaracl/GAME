==============================================
ADR 0001: Internal UUIDs vs. external ids
==============================================

:Status: Accepted

Context
=======

GAME must address records both in its own URLs and through the integrator's
domain keys, without coupling the two namespaces. If GAME exposed the
integrator's keys as primary keys (or vice versa), a rename on either side
would ripple across the boundary.

Decision
========

Every table's primary key is an internal ``UUID``
(``app/model/base_model.py``). Entities additionally carry a caller-owned
external string: ``externalGameId`` (``app/model/games.py``, globally unique),
``externalTaskId`` (``app/model/tasks.py``, unique *per game*, not globally),
and ``externalUserId`` (``app/model/users.py``, globally unique). Internal ids
appear in URLs that address a specific record (``/games/{gameId}/...``);
external ids are how callers reference tasks and users thereafter.

Consequences
============

* Loose coupling and stable external addressing: neither side's renames break
  the other.
* Cost: most calls resolve an external id to its internal UUID first.
* Watch the asymmetry: ``externalGameId`` and ``externalUserId`` are globally
  unique, but ``externalTaskId`` is unique only within its game.

See also
========

* :doc:`/domain-model` - "Identifiers: internal vs. external" is the
  authoritative prose home.
* :doc:`/integrating` - shows the resolve-once-then-use-external pattern.
