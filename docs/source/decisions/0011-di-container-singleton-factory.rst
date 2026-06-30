================================================================
ADR 0011: DI container - db Singleton, repos/services Factories
================================================================

:Status: Accepted

Context
=======

The app needs one shared connection pool per process, but fresh, independently
wired service and repository instances per request - and tests need to swap
the backend without touching endpoint or service code.

Decision
========

Wiring is centralized in one `dependency-injector
<https://python-dependency-injector.ets-labs.org/>`_ container
(``app/core/container.py``). ``db`` is a **Singleton** (one async engine/pool
per process). Repositories and services are **Factories** (a fresh instance per
resolution). A few components are deliberately Singletons because they carry
process-wide state: the DSL execution-log observer, the API-key cache backend,
and the rate-limit counter backend. Endpoints declare what they need with
``Depends(Provide[Container.<provider>])``.

Consequences
============

* Layers are swappable: tests override providers (for example pointing ``db``
  at SQLite) without changing endpoint or service code.
* Cost: every new repository or service needs a provider entry.

See also
========

* :doc:`/architecture` - "Dependency injection".
* :doc:`0012-sqlite-tests-postgres-prod` - the test-time ``db`` override this
  enables.
