=====================
Integrating with GAME
=====================

.. admonition:: Who is this page for?
   :class: note

   Integrators wiring GAME into a product. This is the *task-oriented* guide:
   how to do each thing. For the exhaustive endpoint list see :doc:`rest-api`;
   for scoring logic see :doc:`strategies`.

All paths below are relative to the API base ``/api/v1`` and require
authentication (:doc:`authentication`).

The mental model
================

A typical integration touches four objects in order::

   Game ──contains──► Task ──scored by──► Strategy ──awards──► Points ──► Wallet

You create a **game** once, add **tasks** to it, then report user activity
against tasks to award **points**, which accrue into each user's **wallet**.

Managing games
==============

Create a game
-------------

.. code-block:: bash

   POST /api/v1/games
   {
     "externalGameId": "game-001",
     "platform": "web",
     "strategyId": "default"
   }

* ``externalGameId`` - *your* identifier for the campaign (unique per key).
* ``platform`` - free-form label for where the game runs.
* ``strategyId`` - the **default** strategy for the game's tasks. Use a
  built-in id (e.g. ``default``) or a custom one (``custom:<uuid>``). Omit to
  fall back to ``default``.

The response includes the internal ``gameId`` (UUID) - address the game by
this id thereafter.

Read, update, duplicate, delete
-------------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Operation
     - Endpoint
   * - List games (paginated)
     - ``GET /games``
   * - Get one game
     - ``GET /games/{gameId}``
   * - Update game (partial)
     - ``PATCH /games/{gameId}`` - including switching ``strategyId``
   * - Duplicate a game (with its tasks/params)
     - ``POST /games/{gameId}/duplicate``
   * - Delete a game
     - ``DELETE /games/{gameId}``
   * - Inspect a game's effective strategy
     - ``GET /games/{gameId}/strategy``
   * - List enrolled users
     - ``GET /games/{gameId}/users``

``PATCH`` accepts a ``custom:<uuid>`` strategy id and validates it against the
custom-strategy registry, so you can move a live game onto a DSL strategy
without recreating it.

Managing tasks
==============

Tasks live under a game and inherit its strategy unless they declare their
own.

.. code-block:: bash

   POST /api/v1/games/{gameId}/tasks
   { "externalTaskId": "task-login" }

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Operation
     - Endpoint
   * - Create a task
     - ``POST /games/{gameId}/tasks``
   * - Create many at once
     - ``POST /games/{gameId}/tasks/bulk``
   * - List tasks in a game
     - ``GET /games/{gameId}/tasks``
   * - Get one task (by external id)
     - ``GET /games/{gameId}/tasks/{externalTaskId}``
   * - Update a task (partial)
     - ``PATCH /games/{gameId}/tasks/{taskId}`` - including its params/strategy
   * - Duplicate a task
     - ``POST /games/{gameId}/tasks/{taskId}/duplicate``
   * - Delete a task
     - ``DELETE /games/{gameId}/tasks/{taskId}``

.. note::

   Reads use the **external** task id; mutations that target a specific row
   (PATCH/DELETE/duplicate) use the internal **taskId** (UUID). The
   :doc:`domain-model` explains the internal/external split.

Awarding points
===============

The core write. Report that a user did something worth scoring:

.. code-block:: bash

   POST /api/v1/games/{gameId}/tasks/{externalTaskId}/points
   {
     "externalUserId": "user-123",
     "data": { "event": "task_completed", "source": "mobile-app" },
     "isSimulated": false
   }

Response::

   {
     "points": 1,
     "caseName": "BasicEngagement",
     "isACreatedUser": true,
     "gameId": "4ce32be2-...-0520",
     "externalTaskId": "task-login",
     "created_at": "2026-02-10T12:30:00Z"
   }

Key behaviors:

* **Lazy users** - an unknown ``externalUserId`` is created on the fly;
  ``isACreatedUser`` tells you whether that happened.
* **``data``** - an arbitrary payload passed to the strategy and stored with
  the award. Adaptive strategies read it (e.g. completion time).
* **``caseName``** - the human-readable reason the awarding rule fired; the
  same field appears in analytics.
* **``isSimulated``** - when ``true``, scoring runs but **nothing is
  persisted** (no points, no wallet movement). See :doc:`strategies`.

Idempotency
-----------

Supply an idempotency key (request header, surfaced into the event as
``eventId``) and a retried request will **not** double-award. Pair this with a
correlation id header to trace a request end to end through the logs. This is
what makes point assignment safe to retry on network failure.

Rate limits
-----------

Scoring and action endpoints are rate-limited per API key, per IP, and per
external user, plus a daily quota per key. Exceeding a limit returns ``429``.
Tune the thresholds via the ``ABUSE_*`` variables in :doc:`configuration`;
the model is detailed in :doc:`security`.

Recording explicit actions
--------------------------

Some games award points as a side effect of an action event rather than a
direct points call:

.. code-block:: bash

   POST /api/v1/games/{gameId}/tasks/{externalTaskId}/action
   {
     "typeAction": "TASK_COMPLETED",
     "data": { "durationSeconds": 84, "source": "mobile-app" },
     "description": "User completed the task from mobile flow",
     "externalUserId": "user-123"
   }

This persists a ``UserActions`` record (audit + scoring input) and, when the
game requires it, drives point assignment.

Reading points
==============

GAME exposes aggregates at every granularity:

.. list-table::
   :header-rows: 1
   :widths: 52 48

   * - Question
     - Endpoint
   * - All points in a game (by task & user)
     - ``GET /games/{gameId}/points``
   * - …with per-award detail history
     - ``GET /games/{gameId}/points/details``
   * - One user's total in a game
     - ``GET /games/{gameId}/users/{externalUserId}/points``
   * - All users' points in a task
     - ``GET /games/{gameId}/tasks/{externalTaskId}/points``
   * - …with per-award detail
     - ``GET /games/{gameId}/tasks/{externalTaskId}/points/details``
   * - One user in one task
     - ``GET /games/{gameId}/tasks/{externalTaskId}/users/{externalUserId}/points``
   * - A user's points across everything
     - ``GET /users/{externalUserId}/points``
   * - Bulk/filtered points query
     - ``POST /users/points/query``

Aggregates carry both ``points`` (total) and ``timesAwarded`` (how many
scoring events produced it).

Wallets & the economy
=====================

Each user has exactly one wallet tracking a points balance and a coins
balance, governed by a conversion rate (see :doc:`domain-model`).

.. list-table::
   :header-rows: 1
   :widths: 44 56

   * - Operation
     - Endpoint
   * - Read a user's wallet
     - ``GET /users/{externalUserId}/wallet``
   * - Preview a points→coins conversion
     - ``GET /users/{externalUserId}/convert/preview``
   * - Execute a conversion
     - ``POST /users/{externalUserId}/convert``

Conversions are recorded as ``WalletTransactions`` with the
``appliedConversionRate`` at the time, so the ledger is always reconstructable.

Analytics, KPIs & exports
=========================

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Need
     - Endpoint
   * - Dashboard summary / log feed
     - ``GET /dashboard/summary``, ``GET /dashboard/summary/logs``
   * - Service health
     - ``GET /kpi/health_check``
   * - Data exports (CSV-style history)
     - ``GET /exports/users``, ``/exports/user-points``,
       ``/exports/user-interactions``, ``/exports/wallet-transactions``,
       ``/exports/history``

Export operations are recorded in an ``ExportAuditLog`` for compliance.

A complete integration sketch
=============================

.. code-block:: text

   1. (admin, once)  POST /apikey/create                 → API_KEY
   2.                POST /games                          → gameId
   3.                POST /games/{gameId}/tasks           → task(s)
   4. (optional)     PATCH game/task to attach a strategy (built-in or custom)
   5. (per event)    POST /games/{gameId}/tasks/{externalTaskId}/points
                     with an idempotency key              → points + caseName
   6. (on demand)    GET  …/points and …/wallet           → read state
   7. (optional)     POST /users/{externalUserId}/convert → spend points

Next: :doc:`strategies` to control *how many* points step 5 awards, and
:doc:`rest-api` for the full surface.
