=======================
Configuration Reference
=======================

.. admonition:: Who is this page for?
   :class: note

   Operators. This is the exhaustive reference for **every** environment
   variable read by ``app/core/config.py`` (and a few read elsewhere). For the
   *why* behind the security-related ones, see :doc:`security`.

How configuration works
=======================

* Settings are a Pydantic ``BaseSettings`` class (``Configs``). Values come
  from **environment variables**; a local ``.env`` is loaded automatically in
  development.
* ``ENV`` selects the profile. ``ENV=test`` swaps in ``TestConfigs`` (SQLite,
  localhost DB). ``prod``/``stage`` activate **fail-fast** validation.
* Several values are validated at import time - a bad value raises before the
  app serves a single request (see *Fail-fast guards* below).

.. tip::

   Copy ``.env.sample`` to ``.env`` and edit. In production, inject values
   through the environment or a secret manager - do **not** ship a ``.env``
   with real secrets.

Core / application
==================

.. list-table::
   :header-rows: 1
   :widths: 34 14 52

   * - Variable
     - Default
     - Notes
   * - ``ENV``
     - ``dev``
     - One of ``dev``/``test``/``stage``/``prod``. Gates fail-fast checks,
       log format, and strategy debug output.
   * - ``ROOT_PATH``
     - ``""``
     - ASGI root path when mounted behind a path prefix.
   * - ``API_V1_STR``
     - ``/api/v1``
     - API base path. All documented routes are relative to this.
   * - ``PROJECT_NAME``
     - ``GAME-api``
     - Display name.
   * - ``GAMIFICATIONENGINE_VERSION_APP``
     - ``No_version``
     - Free-form app version label.
   * - ``LOG_LEVEL``
     - ``INFO``
     - Root log level (read in ``app/main.py``).
   * - ``METRICS_ENABLED``
     - ``true``
     - Expose Prometheus ``/metrics``. Disable (or firewall the path) in
       production - it is unauthenticated at the app level. See
       :doc:`observability`.

Database
========

.. list-table::
   :header-rows: 1
   :widths: 34 16 50

   * - Variable
     - Default
     - Notes
   * - ``DB_ENGINE``
     - ``postgresql``
     - SQLAlchemy dialect.
   * - ``DB_USER`` / ``DB_PASSWORD``
     - *(unset)*
     - Credentials.
   * - ``DB_HOST``
     - *(unset)*
     - Hostname.
   * - ``DB_PORT``
     - ``5432``
     - Defaults to PostgreSQL's port (the prior ``3306`` MySQL default
       mismatched the engine).
   * - ``DB_NAME``
     - env-dependent
     - **Required in ``prod``/``stage``** (boot blocks if unset). Defaults to
       ``game_dev_db`` in ``dev`` and ``test_game_dev_db`` in ``test``.
   * - ``DATABASE_URI``
     - derived
     - Assembled from the parts above; usually not set directly.

Connection pool
---------------

.. list-table::
   :header-rows: 1
   :widths: 38 14 48

   * - Variable
     - Default
     - Notes
   * - ``SQLALCHEMY_ECHO``
     - ``false``
     - Log every SQL statement. Dev only.
   * - ``DB_POOL_PRE_PING``
     - ``true``
     - Health-check a connection before use (avoids stale-connection errors).
   * - ``DB_POOL_SIZE``
     - ``20``
     - Persistent pooled connections.
   * - ``DB_MAX_OVERFLOW``
     - ``40``
     - Extra connections allowed above the pool size under burst.
   * - ``DB_POOL_TIMEOUT_SECONDS``
     - ``30``
     - Wait time for a free connection before erroring.
   * - ``DB_POOL_RECYCLE_SECONDS``
     - ``1800``
     - Recycle connections older than this (dodges server-side idle timeouts).

Authentication (Keycloak)
=========================

.. list-table::
   :header-rows: 1
   :widths: 36 22 42

   * - Variable
     - Default
     - Notes
   * - ``KEYCLOAK_URL``
     - ``http://localhost:8080``
     - Public realm base URL (used for issuer + token URLs).
   * - ``KEYCLOAK_URL_DOCKER``
     - ``http://keycloak:8080``
     - In-cluster URL used to fetch the JWKS signing keys.
   * - ``KEYCLOAK_REALM``
     - ``master``
     - Realm name.
   * - ``KEYCLOAK_AUDIENCE``
     - ``account``
     - Required JWT ``aud``; mismatches yield ``403 Invalid audience``.
   * - ``KEYCLOAK_CLIENT_ID``
     - ``admin-cli``
     - OAuth client id (also used by Swagger UI's OAuth flow).
   * - ``KEYCLOAK_CLIENT_SECRET``
     - *(dev placeholder)*
     - **Boot blocks in ``prod``/``stage``** if missing or left at the
       shipped placeholder.
   * - ``SECRET_KEY``
     - ``""``
     - Signs simulation payloads. **Boot blocks in ``prod``/``stage``** if
       empty. (Historically defaulted to the truthy string ``"None"`` - now
       falsy.)

Security: CORS & proxies
========================

.. list-table::
   :header-rows: 1
   :widths: 34 14 52

   * - Variable
     - Default
     - Notes
   * - ``BACKEND_CORS_ORIGINS``
     - ``[]``
     - **Plain comma-separated** allow-list (not JSON), e.g.
       ``https://a.example,https://b.example``. ``*`` is **rejected** in
       ``prod``/``stage``. Middleware attaches only when non-empty.
   * - ``TRUSTED_PROXY_IPS``
     - ``[]``
     - Comma-separated IPs/CIDRs allowed to set ``X-Forwarded-For`` /
       ``X-Real-IP``. Empty = trust no proxy (use socket peer). Malformed
       entries fail at startup. See :doc:`security`.

Abuse prevention & rate limiting
================================

.. list-table::
   :header-rows: 1
   :widths: 40 16 44

   * - Variable
     - Default
     - Notes
   * - ``ABUSE_PREVENTION_ENABLED``
     - ``true``
     - Master switch for rate limiting on sensitive endpoints.
   * - ``ABUSE_RATE_LIMIT_WINDOW_SECONDS``
     - ``60``
     - Short-window length.
   * - ``ABUSE_RATE_LIMIT_PER_API_KEY``
     - ``120``
     - Max requests per key per window.
   * - ``ABUSE_RATE_LIMIT_PER_IP``
     - ``240``
     - Max requests per source IP per window.
   * - ``ABUSE_RATE_LIMIT_PER_EXTERNAL_USER``
     - ``60``
     - Max requests per external user per window.
   * - ``ABUSE_DAILY_QUOTA_PER_API_KEY``
     - ``10000``
     - Daily quota per key for sensitive operations.
   * - ``ABUSE_PREVENTION_BACKEND``
     - ``database``
     - ``database`` or ``redis``. Use ``redis`` for multi-replica (atomic,
       shared, ~100× faster).

Redis (optional, shared state)
==============================

Only needed when a backend below is set to ``redis``.

.. list-table::
   :header-rows: 1
   :widths: 38 22 40

   * - Variable
     - Default
     - Notes
   * - ``REDIS_URL``
     - *(unset)*
     - Connection URL; required when any ``*_BACKEND=redis``.
   * - ``RATE_LIMIT_REDIS_KEY_PREFIX``
     - ``game:rl:``
     - Key namespace for rate-limit counters.
   * - ``RATE_LIMIT_TTL_BUFFER_SECONDS``
     - ``5``
     - Extra TTL slack on counter keys.
   * - ``APIKEY_CACHE_BACKEND``
     - ``memory``
     - ``memory`` (per-worker) or ``redis`` (shared, so revocations propagate
       across workers).
   * - ``APIKEY_CACHE_REDIS_KEY_PREFIX``
     - ``game:apikey:``
     - Key namespace for the API-key cache.
   * - ``API_KEY_HEADER_CACHE_TTL_SECONDS``
     - ``5``
     - How long a key-validation result is cached.

DSL engine limits
=================

.. list-table::
   :header-rows: 1
   :widths: 40 14 46

   * - Variable
     - Default
     - Notes
   * - ``DSL_EXECUTION_TIMEOUT_MS``
     - ``500``
     - Wall-clock backstop per custom-strategy call.
   * - ``DSL_MAX_NODES``
     - ``1000``
     - Max AST nodes (rejected at validation + runtime).
   * - ``DSL_MAX_DEPTH``
     - ``32``
     - Max recursion depth.

DSL execution logging
=====================

.. list-table::
   :header-rows: 1
   :widths: 42 14 44

   * - Variable
     - Default
     - Notes
   * - ``DSL_EXECUTION_LOG_ENABLED``
     - ``true``
     - Persist sampled execution traces.
   * - ``DSL_EXECUTION_LOG_SAMPLE_RATE``
     - ``0.05``
     - Fraction of **successful** runs persisted (errors are always kept).
       ``1.0`` is dev/test only.
   * - ``DSL_EXECUTION_LOG_TRACE_LIMIT``
     - ``200``
     - Max trace entries per row (tail-truncated).
   * - ``DSL_EXECUTION_LOG_QUEUE_MAXSIZE``
     - ``1000``
     - Bounded background-write queue; overflow drops rows (counted by
       ``dsl_execution_log_dropped_total``) instead of slowing scoring.

Errors & extras
===============

.. list-table::
   :header-rows: 1
   :widths: 34 16 50

   * - Variable
     - Default
     - Notes
   * - ``SENTRY_DSN``
     - *(unset)*
     - Enables Sentry when set.
   * - ``SENTRY_ENVIRONMENT``
     - ``dev``
     - Sentry environment tag.
   * - ``SENTRY_RELEASE``
     - ``0.0.0``
     - Sentry release tag.
   * - ``SENTRY_SEND_DEFAULT_PII``
     - ``false``
     - When ``false`` (default) Sentry events carry no PII (user ids, client
       IP, request headers/bodies). Opt in per environment.
   * - ``SENTRY_TRACES_SAMPLE_RATE``
     - ``0.1``
     - Fraction of requests traced for performance. ``< 1.0`` caps cost/volume;
       ``1.0`` (trace everything) is for short local debugging only.
   * - ``SENTRY_PROFILING_ENABLED``
     - ``false``
     - Starts Sentry's continuous profiler only when ``true``.
   * - ``EXTRA_SERVER_URL`` / ``EXTRA_SERVER_DESCRIPTION``
     - *(unset)*
     - Adds an extra server entry to the OpenAPI schema (handy when the API is
       reachable at more than one base URL).
   * - ``DEFAULT_CONVERTION_RATE_POINTS_TO_COIN``
     - ``100``
     - Default points-per-coin used when creating wallets.
   * - ``GOOGLE_ANALYTICS_ACCOUNT``
     - *(unset)*
     - Used by this documentation site's theme only.

Pagination defaults
===================

.. list-table::
   :header-rows: 1
   :widths: 24 14 62

   * - Variable
     - Default
     - Notes
   * - ``PAGE``
     - ``1``
     - Default page for list endpoints.
   * - ``PAGE_SIZE``
     - ``10``
     - Default page size (``page_size=all`` returns everything).
   * - ``ORDERING``
     - ``-id``
     - Default sort (``-`` prefix = descending).

Fail-fast guards (summary)
==========================

These turn misconfiguration into a loud startup failure in ``prod``/``stage``:

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Variable
     - Boot blocks when…
   * - ``SECRET_KEY``
     - empty
   * - ``KEYCLOAK_CLIENT_SECRET``
     - missing or equal to the dev placeholder
   * - ``DB_NAME``
     - unset
   * - ``BACKEND_CORS_ORIGINS``
     - set to ``*``
   * - ``TRUSTED_PROXY_IPS``
     - contains a malformed IP/CIDR (any environment)

Minimal production ``.env`` skeleton
====================================

.. code-block:: ini

   ENV=prod
   SECRET_KEY=<from-secret-manager>

   DB_ENGINE=postgresql
   DB_USER=<user>
   DB_PASSWORD=<from-secret-manager>
   DB_HOST=<host>
   DB_PORT=5432
   DB_NAME=<explicit-db-name>

   KEYCLOAK_URL=https://auth.example.com
   KEYCLOAK_URL_DOCKER=https://auth.example.com
   KEYCLOAK_REALM=game
   KEYCLOAK_AUDIENCE=account
   KEYCLOAK_CLIENT_ID=game-api
   KEYCLOAK_CLIENT_SECRET=<from-secret-manager>

   BACKEND_CORS_ORIGINS=https://app.example.com,https://admin.example.com
   TRUSTED_PROXY_IPS=10.0.0.0/8

   ABUSE_PREVENTION_ENABLED=true
   ABUSE_PREVENTION_BACKEND=redis
   APIKEY_CACHE_BACKEND=redis
   REDIS_URL=redis://redis:6379/0

   METRICS_ENABLED=false   # or keep true and block /metrics at the ingress
