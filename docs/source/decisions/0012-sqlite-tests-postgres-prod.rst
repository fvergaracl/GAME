======================================================
ADR 0012: SQLite in tests, PostgreSQL in production
======================================================

:Status: Accepted

Context
=======

Spinning up real PostgreSQL for every unit and repository test is slow and
infra-heavy. The persistence layer is abstracted enough to swap the backend,
so tests can run against an in-memory database.

Decision
========

Repository and integration tests run the real repositories against an
in-memory ``sqlite+aiosqlite:///:memory:`` engine. A small type shim compiles
the PostgreSQL-specific column types to SQLite equivalents (``UUID`` ->
``CHAR(36)``, ``JSONB`` -> ``JSON``) so production model definitions are used
untouched (``tests/unit_tests/repository/conftest.py``). ``TestConfigs`` is
selected when ``ENV=test``; the ``Database`` wrapper coerces sync URLs to async
drivers and skips pool kwargs for SQLite. The few PostgreSQL-only paths (for
example ``ON CONFLICT DO UPDATE``) fall back to a mocked session.

Consequences
============

* Fast, isolated, no-infra tests for the whole service and repository layer.
* A constraint on contributors: repository queries must stay portable - no
  PostgreSQL-only SQL in the common path.

See also
========

* :doc:`/contributing` - "Testing" documents the SQLite-vs-PostgreSQL split.
* :doc:`0011-di-container-singleton-factory` - the provider override that
  points ``db`` at SQLite.
