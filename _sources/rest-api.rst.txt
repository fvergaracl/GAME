==================
REST API Reference
==================

.. admonition:: Who is this page for?
   :class: note

   Integrators who want the complete endpoint surface in one place. This is a
   curated catalog; the **authoritative, always-current** contract is the
   live OpenAPI schema your deployment serves.

The live, interactive contract
==============================

Every running instance generates its API reference from the code:

.. list-table::
   :header-rows: 1
   :widths: 24 32 44

   * - Tool
     - Path
     - Use it for
   * - **Swagger UI**
     - ``/docs``
     - Try requests in the browser (with OAuth2 login wired in).
   * - **ReDoc**
     - ``/redocs``
     - Clean, readable reference.
   * - **OpenAPI JSON**
     - ``/openapi.json``
     - Generate clients/SDKs.

Each endpoint in the code carries rich OpenAPI metadata - summaries,
per-status response examples, and request/response schemas - so the generated
docs are detailed, not skeletal.

Conventions
===========

* **Base path** - every path below is relative to ``/api/v1``.
* **Auth** - unless noted, endpoints accept ``X-API-Key`` *or* a Keycloak
  bearer token (:doc:`authentication`). A few are OAuth2-only.
* **Ids** - ``{gameId}``/``{taskId}`` are internal UUIDs; ``{externalTaskId}``
  /``{externalUserId}`` are your strings (:doc:`domain-model`).
* **Errors** - ``401`` (no/invalid creds), ``403`` (out of scope / rejected
  key), ``404`` (not found), ``422`` (validation), ``429`` (rate limit),
  ``500`` (server error).

Endpoint catalog
================

API keys (``/apikey``)
----------------------

.. list-table::
   :header-rows: 1
   :widths: 10 38 52

   * -
     - Path
     - Purpose
   * - ``POST``
     - ``/apikey/create``
     - Issue a new API key (OAuth2 + admin).
   * - ``GET``
     - ``/apikey``
     - List API keys.
   * - ``DELETE``
     - ``/apikey/{prefix}``
     - Remove a key by prefix.

Games (``/games``)
------------------

.. list-table::
   :header-rows: 1
   :widths: 10 46 44

   * -
     - Path
     - Purpose
   * - ``GET``
     - ``/games``
     - List games (paginated, scoped).
   * - ``POST``
     - ``/games``
     - Create a game.
   * - ``GET``
     - ``/games/{gameId}``
     - Get one game.
   * - ``PATCH``
     - ``/games/{gameId}``
     - Update a game (incl. ``strategyId``).
   * - ``DELETE``
     - ``/games/{gameId}``
     - Delete a game.
   * - ``POST``
     - ``/games/{gameId}/duplicate``
     - Deep-copy a game with its tasks/params.
   * - ``GET``
     - ``/games/{gameId}/strategy``
     - Inspect the game's effective strategy.
   * - ``GET``
     - ``/games/{gameId}/users``
     - List users enrolled in the game.

Tasks (``/games/{gameId}/tasks``)
---------------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 52 38

   * -
     - Path
     - Purpose
   * - ``POST``
     - ``/games/{gameId}/tasks``
     - Create a task.
   * - ``POST``
     - ``/games/{gameId}/tasks/bulk``
     - Create many tasks.
   * - ``GET``
     - ``/games/{gameId}/tasks``
     - List tasks.
   * - ``GET``
     - ``/games/{gameId}/tasks/{externalTaskId}``
     - Get one task.
   * - ``PATCH``
     - ``/games/{gameId}/tasks/{taskId}``
     - Update a task.
   * - ``DELETE``
     - ``/games/{gameId}/tasks/{taskId}``
     - Delete a task.
   * - ``POST``
     - ``/games/{gameId}/tasks/{taskId}/duplicate``
     - Duplicate a task.

Points & actions (``/games/...``)
---------------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 62 28

   * -
     - Path
     - Purpose
   * - ``POST``
     - ``/games/{gameId}/tasks/{externalTaskId}/points``
     - **Award points** to a user.
   * - ``POST``
     - ``/games/{gameId}/tasks/{externalTaskId}/action``
     - Record a user action (may award points).
   * - ``GET``
     - ``/games/{gameId}/points``
     - All points in a game.
   * - ``GET``
     - ``/games/{gameId}/points/details``
     - …with per-award detail.
   * - ``GET``
     - ``/games/{gameId}/users/{externalUserId}/points``
     - One user's total in a game.
   * - ``GET``
     - ``/games/{gameId}/users/{externalUserId}/points/simulated``
     - Simulated points (**OAuth2-only**, own subject).
   * - ``GET``
     - ``/games/{gameId}/tasks/{externalTaskId}/points``
     - All users' points in a task.
   * - ``GET``
     - ``/games/{gameId}/tasks/{externalTaskId}/points/details``
     - …with detail.
   * - ``GET``
     - ``/games/{gameId}/tasks/{externalTaskId}/users/{externalUserId}/points``
     - One user in one task.

Users, wallets & conversion (``/users``)
----------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 48 42

   * -
     - Path
     - Purpose
   * - ``GET``
     - ``/users/{externalUserId}/points``
     - A user's points everywhere.
   * - ``POST``
     - ``/users/points/query``
     - Bulk/filtered points query.
   * - ``POST``
     - ``/users/external/{externalUserId}/points``
     - Assign points to a user directly.
   * - ``GET``
     - ``/users/{externalUserId}/wallet``
     - Read a user's wallet.
   * - ``GET``
     - ``/users/{externalUserId}/convert/preview``
     - Preview a points→coins conversion.
   * - ``POST``
     - ``/users/{externalUserId}/convert``
     - Execute a conversion.
   * - ``POST``
     - ``/users/{externalUserId}/actions``
     - Record a user action.

Strategies (built-in) (``/strategies``)
---------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 40 50

   * -
     - Path
     - Purpose
   * - ``GET``
     - ``/strategies``
     - List available strategies.
   * - ``GET``
     - ``/strategies/{id}``
     - Strategy metadata.
   * - ``GET``
     - ``/strategies/{id}/schema``
     - Configurable variables.
   * - ``GET``
     - ``/strategies/{id}/graph``
     - Rendered logic graph.

Custom strategies / DSL (``/strategies/custom``)
------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 52 38

   * -
     - Path
     - Purpose
   * - ``POST`` / ``GET``
     - ``/strategies/custom``
     - Create / list custom strategies.
   * - ``GET`` / ``PUT``
     - ``/strategies/custom/{id}``
     - Get / update (new draft).
   * - ``POST``
     - ``/strategies/custom/{id}/publish``
     - Publish a version.
   * - ``POST``
     - ``/strategies/custom/{id}/archive``
     - Archive.
   * - ``GET``
     - ``/strategies/custom/{id}/versions``
     - List versions.
   * - ``POST``
     - ``/strategies/custom/{id}/rollback/{version}``
     - Roll back.
   * - ``GET``
     - ``/strategies/custom/{id}/usage``
     - Where it's used.
   * - ``POST``
     - ``/strategies/custom/simulate``
     - Simulate an ad-hoc AST.
   * - ``POST``
     - ``/strategies/custom/{id}/simulate``
     - Simulate a stored strategy.
   * - ``GET``
     - ``/strategies/custom/templates``
     - Starter templates.
   * - ``POST``
     - ``/strategies/custom/import``
     - Import a strategy.
   * - ``GET``
     - ``/strategies/custom/{id}/metrics``
     - Per-strategy execution metrics.
   * - ``GET``
     - ``/strategies/custom/compare``
     - A/B comparison.

Analytics, exports & ops
------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 40 50

   * -
     - Path
     - Purpose
   * - ``GET``
     - ``/kpi/health_check``
     - Service health/readiness.
   * - ``GET``
     - ``/dashboard/summary``
     - Dashboard summary.
   * - ``GET``
     - ``/dashboard/summary/logs``
     - Recent log feed.
   * - ``GET``
     - ``/exports/users``
     - Export users.
   * - ``GET``
     - ``/exports/user-points``
     - Export user points.
   * - ``GET``
     - ``/exports/user-interactions``
     - Export interactions.
   * - ``GET``
     - ``/exports/wallet-transactions``
     - Export wallet ledger.
   * - ``GET``
     - ``/exports/history``
     - Export audit history.

.. note::

   This catalog is maintained by hand for orientation. When in doubt, trust
   ``/openapi.json`` from your deployment - it is generated from the code and
   cannot drift.
