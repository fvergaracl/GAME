========
Security
========

.. admonition:: Who is this page for?
   :class: note

   Operators and security reviewers. It collects every enforcement boundary in
   one place. Credential *usage* is in :doc:`authentication`; the scoring
   sandbox is in :doc:`dsl-engine`.

Threat model in one paragraph
=============================

GAME is a multi-tenant scoring backend reachable by many API keys and OAuth
identities. The properties it defends: (a) one tenant cannot read or mutate
another's data; (b) a flood of requests cannot exhaust the service or skew
scoring; (c) user-supplied strategies cannot execute arbitrary code or run
away with resources; and (d) a misconfiguration cannot silently downgrade
these guarantees in production.

Authentication
==============

Two credentials, resolved API-key-first then OAuth2, validated strictly
(RS256 JWTs with issuer/audience/expiry checks). The full mechanism, failure
codes, and the ``AdministratorGAME`` admin role are documented in
:doc:`authentication`.

Authorization & data scoping
============================

Authentication answers *who*; authorization answers *what they may touch*.
Scoping is enforced in the **service layer** (``app/services/game_access.py``)
using the ``AuthContext`` carried from the endpoint, so every code path goes
through the same rules:

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Principal
     - Visibility
   * - **Admin** (``AdministratorGAME``)
     - Every game and every user. Bypasses scoping.
   * - **API key**
     - Scoped to rows whose ``apiKey_used`` matches the key - i.e. the data
       *that key created*. A key cannot read another key's games/users.
   * - **OAuth non-admin**
     - Scoped to games whose ``oauth_user_id`` matches the token subject;
       per-user data is gated at the game level.

The enforcement helpers raise precise errors:

* ``get_authorized_game`` → ``404 Game not found`` if it doesn't exist,
  ``403 You do not have permission to access this game`` if it exists but is
  out of scope.
* ``get_authorized_user`` → analogous, for user-addressed endpoints.

Because the check lives below the HTTP layer, adding a new endpoint that
forgets to scope is a *visible* omission - the service method it calls demands
the scoping kwargs.

Abuse prevention & rate limiting
================================

Sensitive write endpoints (point assignment, action recording) pass through
``AbusePreventionService`` before doing work. It enforces, per request:

.. list-table::
   :header-rows: 1
   :widths: 44 18 38

   * - Limit
     - Default
     - Env var
   * - Short-window requests per API key
     - 120 / 60 s
     - ``ABUSE_RATE_LIMIT_PER_API_KEY``
   * - Short-window requests per IP
     - 240 / 60 s
     - ``ABUSE_RATE_LIMIT_PER_IP``
   * - Short-window requests per external user
     - 60 / 60 s
     - ``ABUSE_RATE_LIMIT_PER_EXTERNAL_USER``
   * - Daily quota per API key
     - 10 000 / day
     - ``ABUSE_DAILY_QUOTA_PER_API_KEY``
   * - Window length
     - 60 s
     - ``ABUSE_RATE_LIMIT_WINDOW_SECONDS``

Over-limit requests get ``429`` with a descriptive detail. The whole subsystem
can be turned off with ``ABUSE_PREVENTION_ENABLED=false`` (not recommended in
production).

Counter backend
---------------

The counter store is pluggable via ``ABUSE_PREVENTION_BACKEND``:

* ``database`` (default) - increments a row in ``AbuseLimitCounter``. Simple,
  but a hot row under load.
* ``redis`` - atomic ``INCR`` + ``EXPIRE`` against ``REDIS_URL`` (~50 µs vs.
  ~5 ms for the Postgres UPDATE, and naturally shared across instances).
  Recommended for multi-replica deployments.

Trusted proxies (don't let clients forge their IP)
--------------------------------------------------

Per-IP limits are only meaningful if the client IP can be trusted. When GAME
runs behind a reverse proxy/ingress, the real client IP arrives in
``X-Forwarded-For`` / ``X-Real-IP`` - headers a client could otherwise forge to
dodge per-IP limits.

``TRUSTED_PROXY_IPS`` is the gate. It is a comma-separated list of IPs/CIDRs
allowed to set forwarding headers:

* **Empty (default)** - no proxy is trusted; forwarding headers are ignored and
  the socket peer is used. This is the secure default.
* **Set** to your proxy/ingress IP(s) - only then are forwarding headers
  honored.

Malformed entries are rejected **at startup**, so a typo fails fast instead of
silently trusting no one.

CORS
====

CORS origins come from ``BACKEND_CORS_ORIGINS`` (a plain comma-separated list,
not JSON). The middleware is only attached when origins are configured.

Two safety behaviors:

* **Wildcard is rejected in protected environments.** With ``ENV=prod`` or
  ``stage``, ``BACKEND_CORS_ORIGINS=*`` raises at startup - a wildcard combined
  with credentialed requests would let any site act on the user's behalf.
* **CORS wraps the error handler.** The middleware ordering (see
  :doc:`architecture`) guarantees even a ``500`` carries CORS headers, so the
  browser surfaces the real status instead of a bare "Network Error".

Secrets & fail-fast configuration
=================================

In ``prod``/``stage`` the app **refuses to boot** when a security-critical
setting is missing or left at an insecure default:

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Guard
     - Boot blocks if…
   * - ``SECRET_KEY``
     - empty. (It previously defaulted to the literal string ``"None"`` -
       truthy - which silently signed payloads with the word "None". Now it
       resolves to ``""`` and is rejected in protected envs.)
   * - ``KEYCLOAK_CLIENT_SECRET``
     - missing or equal to the shipped dev placeholder.
   * - ``DB_NAME``
     - unset. (Prevents prod/stage workloads from silently writing to a
       database named ``game_dev_db`` when ``DB_HOST`` is repointed.)
   * - ``BACKEND_CORS_ORIGINS``
     - set to ``*``.

These checks run once at import of ``app.core.config`` and turn a class of
"works in dev, leaks in prod" mistakes into loud startup failures.

.. important::

   Manage secrets via the environment or a secret manager - **never** commit
   real secrets, and don't ship a ``.env`` with production values. See
   :doc:`configuration`.

Strategy sandbox
================

User-authored DSL strategies are the largest attack surface and get their own
defenses: a validator that whitelists every node/op/field and bounds size, and
an interpreter with no ``eval``/``exec``/``getattr``, frozen field access, and
a cancellable wall-clock timeout. See :doc:`dsl-engine`.

Auditability
============

* Every write stamps ``apiKey_used`` / ``oauth_user_id`` (the ``BaseModel``
  contract), so any row's origin is known.
* Endpoints emit structured audit logs (``AuditLogger``) with correlation ids.
* Data exports are recorded in ``ExportAuditLog``.
* DSL runs are sampled into ``StrategyExecutionLog``.

Hardening checklist
===================

.. list-table::
   :header-rows: 1
   :widths: 6 94

   * - ✓
     - Item
   * -
     - ``ENV=prod`` (or ``stage``) so fail-fast checks are active.
   * -
     - ``SECRET_KEY`` and ``KEYCLOAK_CLIENT_SECRET`` set to strong, unique
       values from a secret manager.
   * -
     - ``BACKEND_CORS_ORIGINS`` an explicit allow-list (never ``*``).
   * -
     - ``TRUSTED_PROXY_IPS`` set to your ingress/proxy IP(s) when behind one.
   * -
     - ``ABUSE_PREVENTION_ENABLED=true``; ``ABUSE_PREVENTION_BACKEND=redis``
       for multi-replica.
   * -
     - ``APIKEY_CACHE_BACKEND=redis`` so key revocations propagate across
       workers.
   * -
     - ``/metrics`` not exposed publicly (front it at the ingress, or set
       ``METRICS_ENABLED=false``).
   * -
     - One API key per integration/``client`` to bound blast radius.
