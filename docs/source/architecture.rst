============
Architecture
============

.. admonition:: Who is this page for?
   :class: note

   Contributors and operators who need an accurate mental model of how a
   request flows through GAME and why the layers are split the way they are.
   Integrators can skip to :doc:`integrating`.

The layered design
==================

GAME is a layered application. Each layer has exactly one responsibility and
talks only to the layer directly beneath it::

    HTTP request
        │
        ▼
   ┌─────────────┐   FastAPI routers in app/api/v1/endpoints/*
   │  Endpoint   │   • validation (Pydantic schemas)
   │   layer     │   • authentication & scoping
   └─────────────┘   • request/response shaping, audit logging
        │
        ▼
   ┌─────────────┐   app/services/*
   │  Service    │   • business logic, transactional behavior
   │   layer     │   • orchestration across repositories
   └─────────────┘   • domain rules and invariants
        │
        ├───────────────► ┌───────────────┐  app/engine/*
        │                 │ Strategy      │  • scoring strategies
        │                 │ engine        │  • built-ins + sandboxed DSL
        │                 └───────────────┘
        ▼
   ┌─────────────┐   app/repository/*
   │ Repository  │   • persistence abstraction
   │   layer     │   • SQLAlchemy 2.0 async queries
   └─────────────┘   • no business logic
        │
        ▼
   ┌─────────────┐   PostgreSQL (async, via asyncpg)
   │  Database   │
   └─────────────┘

The same boundaries appear in the directory tree:

.. list-table::
   :header-rows: 1
   :widths: 26 30 44

   * - Layer
     - Package
     - Responsibility
   * - Endpoint
     - ``app/api/v1/endpoints/``
     - HTTP interface: routing, request validation, authentication,
       per-request audit logging, mapping domain errors to HTTP responses.
   * - Service
     - ``app/services/``
     - Business logic and orchestration. The *only* place transactions and
       multi-repository workflows live.
   * - Strategy engine
     - ``app/engine/``
     - Adaptive/deterministic scoring. Pluggable strategies selected by
       ``strategyId``; includes the DSL interpreter and validator.
   * - Repository
     - ``app/repository/``
     - Thin persistence layer over SQLAlchemy ``AsyncSession``. CRUD and
       queries only — no domain decisions.
   * - Model
     - ``app/model/``
     - SQLModel/SQLAlchemy table definitions (the database schema).
   * - Schema
     - ``app/schema/``
     - Pydantic request/response contracts (the wire format).

Why this split matters:

* **Pluggable strategies** — scoring logic is isolated in ``app/engine`` and
  selected by id, so new strategies drop in without touching endpoints or
  repositories.
* **Deterministic services** — business rules live in one layer, making them
  unit-testable without HTTP or a real database.
* **Reproducible behavior** — persistence is abstracted, so the same service
  logic runs against PostgreSQL in production and SQLite in tests.

The life of a scoring request
=============================

Tracing ``POST /api/v1/games/{gameId}/tasks/{externalTaskId}/points`` end to
end (see ``app/api/v1/endpoints/games_points.py``):

#. **Middleware** — the request passes through the outer middleware stack
   (CORS → unhandled-error catcher; see below) and, if metrics are enabled,
   the Prometheus instrumentator.
#. **Auth dependency** — ``Depends(auth_api_key_or_oauth2)`` resolves an
   ``X-API-Key`` header *or* an OAuth2 bearer token. Failure short-circuits
   with ``401``/``403`` before any business logic runs.
#. **Audit context** — ``Depends(audit_log("game"))`` builds an
   ``AuditLogger`` bound to the authenticated principal (API key, OAuth user
   id, admin flag). Every meaningful step is logged with a correlation id.
#. **Validation** — the JSON body is parsed into a Pydantic schema
   (``AsignPointsToExternalUserId``); malformed input yields ``422`` before
   the handler body executes.
#. **Abuse prevention** — ``AbusePreventionService`` enforces per-API-key,
   per-IP, and per-user rate limits and daily quotas; over-limit yields
   ``429`` (see :doc:`security`).
#. **Service** — ``UserPointsService.assign_points_to_user`` orchestrates the
   work: resolve/lazily-create the user, load the task's effective strategy,
   run scoring, persist ``UserPoints``, and move the wallet — within a
   transaction.
#. **Strategy engine** — the resolved strategy computes ``points`` and a
   ``caseName``. For custom strategies this runs the sandboxed DSL
   interpreter (:doc:`dsl-engine`).
#. **Repository** — persistence happens through repositories over an async
   session; idempotency keys prevent double-awards on retry.
#. **Response** — the service returns a domain object serialized by the
   response model. On any exception the endpoint maps it to a structured
   error (preserving the correlation id) and records an audit error.

The middleware stack (and a subtle ordering bug it fixes)
=========================================================

Middleware is registered in ``app/main.py``. FastAPI's ``add_middleware``
*prepends*, so the **last** registered middleware is the **outermost**. GAME
relies on this on purpose::

    add_middleware(CatchUnhandledErrorsMiddleware)   # registered first
    add_middleware(CORSMiddleware)                   # registered second → outermost

The CORS layer must wrap the error-catcher so that when an unhandled
exception is rendered as a ``500`` *from inside* the stack, the response
still passes back through CORS and receives its ``Access-Control-Allow-*``
headers. Without this ordering the browser blocks the error response and the
dashboard shows a bare *"Network Error"* with no clue that the real cause was
a backend ``500``.

.. admonition:: Operator tip
   :class: tip

   A dashboard "Network Error" with no HTTP status almost always means a
   backend ``500`` whose body the browser dropped. Check the API logs
   (``docker logs GAME_API_DEV``) for the real traceback rather than trusting
   the browser message.

Dependency injection
====================

Wiring is centralized in a single `dependency-injector
<https://python-dependency-injector.ets-labs.org/>`_ container,
``app/core/container.py``:

* ``db`` is a **Singleton** — one async engine/connection pool per process.
* Repositories and services are **Factories** — a fresh instance per
  resolution, each handed the dependencies it declares.
* A few components are deliberately **Singletons** because they carry
  process-wide state: the DSL execution-log observer (its sampling RNG and
  background queue), the API-key cache backend, and the rate-limit counter
  backend.

Endpoints never construct services directly. They declare what they need with
``Depends(Provide[Container.<provider>])`` and the container supplies a fully
wired instance. The ``wiring_config`` in the container lists exactly which
endpoint modules participate in injection.

This is what makes the layers swappable: tests override providers (for
example pointing ``db`` at SQLite) without changing a line of endpoint or
service code.

Async & persistence model
=========================

* The application is **async end to end** — FastAPI handlers, services, and
  repositories are coroutines; persistence uses SQLAlchemy 2.0's
  ``AsyncSession`` over ``asyncpg``.
* ``BaseRepository`` (``app/repository/base_repository.py``) provides the
  common CRUD vocabulary — ``read_by_id``, ``read_by_options`` (paginated +
  filtered + ordered), ``read_by_column(s)``, ``create``, ``update``,
  ``whole_update``, ``delete_by_id`` — each opening a session from the
  injected ``session_factory``.
* ``create`` supports an **externally managed session** (``auto_commit=False``)
  so a service can compose several writes into one transaction; the default
  path commits per call.
* Connection pooling is configured on the singleton engine (pool size,
  overflow, pre-ping, recycle) and tuned via environment variables — see
  :doc:`configuration`.

Because the app holds no per-request server state beyond the database, it is
**stateless and horizontally scalable**: run N replicas behind a load
balancer and let PostgreSQL (and optionally Redis) be the shared state.

Cross-cutting concerns
======================

These are not layers but slices that cut across the stack; each has its own
page:

* **Authentication & authorization** → :doc:`authentication`, :doc:`security`
* **Rate limiting & abuse prevention** → :doc:`security`
* **Observability** (metrics, logs, Sentry, execution traces) →
  :doc:`observability`
* **Configuration** (every environment variable) → :doc:`configuration`

Where to go next
================

* :doc:`domain-model` — the entities these layers move around.
* :doc:`dsl-engine` — the strategy engine in depth.
* :doc:`codebase` — the auto-generated API reference for every module.
