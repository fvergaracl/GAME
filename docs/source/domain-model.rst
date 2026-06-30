============
Domain Model
============

.. admonition:: Who is this page for?
   :class: note

   Integrators who need to know what each object means on the wire, and
   contributors who need the schema. This page is canonical for the domain
   model: the rendered entity-relationship diagram below plus the prose
   reference that follows.

The big picture
===============

GAME's entities fall into five clusters - identity/access, the campaign
hierarchy, participation & scoring, the economy, and strategy/observability.
The entity-relationship diagram below is the canonical schema: every table in
``app/model/`` with its columns and keys. Solid lines are foreign-key
relationships; dashed lines are **soft references** resolved by string id
(``strategyId``), which carry no database foreign key on purpose so a strategy
can be hard-deleted without cascading away its history.

.. mermaid::

   erDiagram

       %% --- Authentication & access control ---
       OAuthUsers {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      provider
           string      provider_user_id UK
           string      status
           string      apiKey_used      FK
       }
       ApiKey {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      apiKey           UK
           string      client
           string      description
           bool        active
           string      createdBy
           string      oauth_user_id    FK
       }

       %% --- Core domain: users ---
       Users {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      externalUserId   UK
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }

       %% --- Core domain: campaigns (games & tasks) ---
       Games {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      externalGameId   UK
           string      strategyId
           string      platform
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }
       GameParams {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      key
           string      value
           UUID        gameId           FK
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }
       Tasks {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      externalTaskId
           UUID        gameId           FK
           string      strategyId
           string      status
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }
       TaskParams {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      key
           string      value
           UUID        taskId           FK
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }

       %% --- User <-> game participation ---
       UserGameConfig {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           UUID        userId           FK
           UUID        gameId           FK
           string      experimentGroup
           json        configData
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }
       UserActions {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      typeAction
           jsonb       data
           string      description
           UUID        userId           FK
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }
       UserInteractions {
           UUID        id                PK
           datetime_tz created_at
           datetime_tz updated_at
           UUID        userId            FK
           UUID        taskId            FK
           string      interactionType
           string      interactionDetail
           string      apiKey_used       FK
           string      oauth_user_id     FK
       }
       UserPoints {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           int         points
           string      caseName
           string      idempotencyKey
           jsonb       data
           string      description
           UUID        userId           FK
           UUID        taskId           FK
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }

       %% --- Wallet & economy ---
       Wallet {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           float       coinsBalance
           float       pointsBalance
           int         conversionRate
           UUID        userId           FK "UK"
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }
       WalletTransactions {
           UUID        id                    PK
           datetime_tz created_at
           datetime_tz updated_at
           string      transactionType
           int         points
           float       coins
           jsonb       data
           float       appliedConversionRate
           UUID        walletId              FK
           string      apiKey_used           FK
           string      oauth_user_id         FK
       }

       %% --- Strategy authoring (DSL) ---
       StrategyDefinition {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      realmId
           string      name
           string      description
           string      type
           string      parentStrategyId
           jsonb       astJson
           text        blocklyXml
           int         version
           string      status
           string      createdBy
           datetime_tz publishedAt
           string      experimentTag
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }

       %% --- Observability & operations ---
       StrategyExecutionLog {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      strategyId
           int         strategyVersion
           string      strategyType
           string      realmId
           string      externalGameId
           string      externalTaskId
           string      externalUserId
           string      status
           string      errorCode
           numeric     points
           string      caseName
           numeric     durationMs
           int         nodesExecuted
           jsonb       trace
           bool        sampled
           string      parentStrategyId
           text        notes
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }
       ApiRequests {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           UUID        userId           FK
           string      endpoint
           int         statusCode
           int         responseTimeMS
           string      requestType
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }
       Logs {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      log_level
           string      message
           string      module
           json        details
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }
       KpiMetrics {
           UUID        id                     PK
           datetime_tz created_at
           datetime_tz updated_at
           string      day
           int         totalRequests
           int         successRate
           int         avgLatencyMS
           int         errorRate
           int         activeUsers
           int         retentionRate
           int         avgInteractionsPerUser
           string      apiKey_used            FK
           string      oauth_user_id          FK
       }
       UptimeLogs {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      status
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }
       ExportAuditLog {
           UUID        id               PK
           datetime_tz created_at
           datetime_tz updated_at
           string      datasetType
           string      format
           jsonb       filters
           int         rowLimit
           int         rowCount
           string      status
           string      requestedBy
           string      apiKey_used      FK
           string      oauth_user_id    FK
       }

       %% --- Rate limiting ---
       AbuseLimitCounter {
           UUID        id          PK
           datetime_tz created_at
           datetime_tz updated_at
           string      scopeType
           string      scopeValue
           string      windowName
           datetime_tz windowStart
           int         counter
       }

       %% --- Relationships ---
       OAuthUsers      ||--o{ ApiKey               : "owns"

       %% ApiKey audit trail: every BaseModel row records the key that wrote it
       ApiKey          ||--o{ Users                : "audit"
       ApiKey          ||--o{ Games                : "audit"
       ApiKey          ||--o{ GameParams           : "audit"
       ApiKey          ||--o{ Tasks                : "audit"
       ApiKey          ||--o{ TaskParams           : "audit"
       ApiKey          ||--o{ UserGameConfig       : "audit"
       ApiKey          ||--o{ UserActions          : "audit"
       ApiKey          ||--o{ UserInteractions     : "audit"
       ApiKey          ||--o{ UserPoints           : "audit"
       ApiKey          ||--o{ Wallet               : "audit"
       ApiKey          ||--o{ WalletTransactions   : "audit"
       ApiKey          ||--o{ StrategyDefinition   : "audit"
       ApiKey          ||--o{ StrategyExecutionLog : "audit"
       ApiKey          ||--o{ ApiRequests          : "audit"
       ApiKey          ||--o{ Logs                 : "audit"
       ApiKey          ||--o{ KpiMetrics           : "audit"
       ApiKey          ||--o{ UptimeLogs           : "audit"
       ApiKey          ||--o{ ExportAuditLog       : "audit"

       %% Campaign hierarchy
       Games           ||--o{ GameParams           : "parameterized by"
       Games           ||--o{ Tasks                : "contains"
       Tasks           ||--o{ TaskParams           : "parameterized by"

       %% User participation
       Games           ||--o{ UserGameConfig       : "configures"
       Users           ||--o{ UserGameConfig       : "enrolled in"
       Users           ||--o{ UserActions          : "performs"
       Users           ||--o{ UserInteractions     : "has"
       Tasks           ||--o{ UserInteractions     : "tracked by"
       Users           ||--o{ UserPoints           : "earns"
       Tasks           ||--o{ UserPoints           : "awards"

       %% Economy
       Users           ||--|| Wallet               : "owns"
       Wallet          ||--o{ WalletTransactions   : "records"

       %% Strategy (soft references by string id, no DB FK)
       StrategyDefinition ||..o{ StrategyExecutionLog : "executions"
       StrategyDefinition |o..o{ Games                : "custom strategyId"
       StrategyDefinition |o..o{ Tasks                : "custom strategyId"

       %% Observability
       Users           ||--o{ ApiRequests          : "makes"

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
