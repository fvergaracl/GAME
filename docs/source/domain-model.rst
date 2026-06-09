============
Domain Model
============

.. admonition:: Who is this page for?
   :class: note

   Integrators who need to know what each object means on the wire, and
   contributors who need the schema. The canonical machine-readable ERD
   (Mermaid) lives in ``docs/domain-model.md``; this page is the prose
   reference.

The big picture
===============

GAME's entities fall into five clusters. Solid arrows below read
"parent → many children"::

   AUTH / ACCESS            CAMPAIGN HIERARCHY
   ┌──────────┐             ┌──────────┐
   │OAuthUsers│◄──owns────► │  Games   │──┬──► GameParams   (key/value config)
   └────┬─────┘   ┌────────►└────┬─────┘  └──► Tasks ──► TaskParams
        │         │              │
        ▼         │              ▼
   ┌──────────┐   │        ┌──────────────┐
   │  ApiKey  │───┘        │UserGameConfig│  (enrolment + experiment group)
   └────┬─────┘            └──────────────┘
        │ audit trail: every entity records the ApiKey that created it
        ▼
   PARTICIPATION & SCORING                 ECONOMY
   ┌──────────┐                            ┌──────────┐
   │  Users   │──► UserActions             │  Wallet  │──► WalletTransactions
   │          │──► UserInteractions        └────▲─────┘
   │          │──► UserPoints ◄──awards──┐       │ one wallet per user
   │          │──────────────────────────┴───────┘
   └──────────┘
                STRATEGY                    OBSERVABILITY
   ┌────────────────────┐                  ApiRequests · Logs · KpiMetrics
   │ StrategyDefinition │──► versions      UptimeLogs · StrategyExecutionLog
   │ (custom DSL)       │                  AbuseLimitCounter · ExportAuditLog
   └────────────────────┘

Core entities
=============

Identity & access
-----------------

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Entity
     - Meaning
   * - **OAuthUsers**
     - A human/admin identity federated from Keycloak (``provider`` +
       ``provider_user_id``). Owns API keys and is the principal behind
       OAuth2-authenticated requests.
   * - **ApiKey**
     - A machine credential (``apiKey``, ``client``, ``active``) issued to a
       caller. Every write records *which key created it*, giving a complete
       audit trail and the basis for per-key data scoping.

Campaign hierarchy
------------------

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Entity
     - Meaning
   * - **Games**
     - A campaign/project. Carries an ``externalGameId`` (your identifier), a
       ``platform``, and a ``strategyId`` - the *default* scoring strategy for
       its tasks. If unset, the built-in ``default`` strategy applies.
   * - **GameParams**
     - Key/value configuration attached to a game (e.g. base points). These
       feed strategy variables.
   * - **Tasks**
     - A concrete activity inside a game (``externalTaskId``). A task inherits
       the game's strategy unless it declares its own ``strategyId``. Tasks
       are independent of each other.
   * - **TaskParams**
     - Key/value configuration attached to a task; overrides/extends game
       params for that task's scoring.

Participation & scoring
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Entity
     - Meaning
   * - **Users**
     - A participant, keyed by your ``externalUserId``. Users are created
       lazily on first scoring if they don't exist yet.
   * - **UserGameConfig**
     - A user's enrolment in a game, including their ``experimentGroup``
       (e.g. control vs. treatment for A/B studies) and per-user
       ``configData``.
   * - **UserActions**
     - An explicit event a user performed (``typeAction`` + structured
       ``data``), recorded for audit and as scoring input.
   * - **UserInteractions**
     - A typed interaction between a user and a task
       (``interactionType``/``interactionDetail``).
   * - **UserPoints**
     - The heart of the system: one row per award. Holds ``points``, the
       ``caseName`` (why the rule matched), an ``idempotencyKey`` (dedupes
       retries), the originating ``data``, and links to user + task.

Economy
-------

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Entity
     - Meaning
   * - **Wallet**
     - Exactly one per user. Tracks ``pointsBalance`` and ``coinsBalance``
       plus the ``conversionRate`` (points per coin).
   * - **WalletTransactions**
     - An append-only ledger of wallet movements (``transactionType``,
       ``points``, ``coins``, ``appliedConversionRate``), so balances are
       always reconstructable.

Strategy & observability
------------------------

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Entity
     - Meaning
   * - **StrategyDefinition**
     - A custom, DSL-authored strategy and its versions. Saving a published
       version creates a new ``DRAFT`` rather than overwriting (see
       :doc:`strategies`). Referenced by ``strategyId = custom:<uuid>``.
   * - **StrategyExecutionLog**
     - A sampled trace of a custom-strategy run: status, latency, node count,
       case name, error code, and (bounded) node-by-node trace. Drives the
       observability dashboard.
   * - **ApiRequests / Logs / KpiMetrics / UptimeLogs**
     - Operational telemetry: per-request records, structured application
       logs, daily KPI rollups, and uptime samples.
   * - **AbuseLimitCounter**
     - Backing store for the database rate-limiter (scope, window, counter).
       See :doc:`security`.
   * - **ExportAuditLog**
     - Records data-export operations for compliance/audit.

The ``BaseModel`` contract
==========================

Every persisted entity inherits a common base (``app/model/base_model.py``)
that contributes four columns to *every* table:

.. list-table::
   :header-rows: 1
   :widths: 22 18 60

   * - Column
     - Type
     - Notes
   * - ``id``
     - ``UUID``
     - Primary key, server-generated.
   * - ``created_at``
     - ``datetime`` (tz-aware UTC)
     - Set on insert. Stored as timezone-aware UTC.
   * - ``updated_at``
     - ``datetime`` (tz-aware UTC)
     - Refreshed on update.
   * - ``apiKey_used`` / ``oauth_user_id``
     - FK / string
     - The credential that performed the write - the audit + scoping anchor.

Because ``apiKey_used`` is stamped on every write, GAME can answer "who
created this?" for any row and can *scope* reads so one API key only sees the
data it created (admins bypass scoping). See :doc:`security`.

Identifiers: internal vs. external
==================================

GAME maintains a clean separation between **its** identifiers and **yours**:

* **Internal** ids are ``UUID`` primary keys (``gameId``, ``taskId``,
  ``userId``). They appear in URLs that address a specific record
  (``/games/{gameId}/...``).
* **External** ids are the strings *you* supply (``externalGameId``,
  ``externalTaskId``, ``externalUserId``). They let you address records using
  your own domain keys and keep GAME loosely coupled to your system.

A common integration pattern: create a game and keep the returned
``gameId``; thereafter reference tasks and users by *your* external ids.

Idempotency & concurrency
=========================

* Point assignment accepts an **idempotency key** (request header, surfaced
  into the event ``data`` as ``eventId``). A repeated request with the same
  key does not create a second ``UserPoints`` row - safe to retry.
* Writes are **transactional**; wallet movement and points persistence happen
  together so a partial failure does not leave a points row without its
  wallet effect.

Where to go next
================

* :doc:`integrating` - the request/response shapes for creating games, tasks,
  and awarding points.
* :doc:`strategies` - how ``strategyId`` resolution and scoring actually work.
* :doc:`codebase` - the generated reference for ``app/model`` and the rest.
