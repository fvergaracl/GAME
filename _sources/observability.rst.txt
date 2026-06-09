=============
Observability
=============

.. admonition:: Who is this page for?
   :class: note

   Operators running GAME and contributors adding instrumentation. Pairs with
   :doc:`operations` (how to run the stack) and :doc:`configuration` (every
   knob).

The four signals
================

GAME exposes the usual observability signals plus a domain-specific one
(strategy execution traces):

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Signal
     - Where
   * - **Metrics**
     - Prometheus ``/metrics`` (HTTP + DSL counters).
   * - **Logs**
     - Structured stdout (JSON in prod/stage) + persisted ``Logs`` audit
       trail.
   * - **Errors**
     - Sentry (when ``SENTRY_DSN`` is set).
   * - **Traces (domain)**
     - Sampled ``StrategyExecutionLog`` rows for custom-strategy runs.

Metrics (Prometheus)
====================

When ``METRICS_ENABLED=true`` (the default), the app mounts
``prometheus_fastapi_instrumentator`` at ``/metrics``. It is wired *after*
CORS but *before* the routers, so it observes every request middleware yet
does not sit behind router-level auth — i.e. ``/metrics`` itself is unguarded
at the app level and must be protected at the ingress (or disabled) in
production.

You get out of the box:

* **HTTP metrics** — request counts, durations, and status classes
  (status codes are grouped; untemplated paths and ``/metrics`` are excluded).
* **DSL metrics** — custom counters defined in ``app/engine/dsl_metrics.py``,
  which live in the default ``prometheus_client`` registry and are therefore
  exported automatically:

.. list-table::
   :header-rows: 1
   :widths: 46 54

   * - Metric
     - Meaning
   * - ``dsl_execution_duration_seconds``
     - Histogram of custom-strategy execution wall-clock.
   * - ``dsl_execution_nodes_total``
     - AST nodes visited per run (cost signal).
   * - ``dsl_execution_errors_total``
     - Failed strategy executions, by error type.
   * - ``dsl_execution_log_dropped_total``
     - Execution-log rows dropped because the persistence queue was full
       (see below). **Non-zero = the sink is saturated**, not that scoring is
       at risk.

The bundled Compose stack ships a pre-configured Prometheus that scrapes these
without extra wiring.

Logging
=======

Logging is configured at startup (``app/main.py``):

* **Format** — plain text in ``dev``; structured **JSON** in ``prod``/``stage``
  (via ``python-json-logger``), with renamed fields
  (``timestamp``/``level``/``logger``) ready for ingestion.
* **Level** — ``LOG_LEVEL`` env var (default ``INFO``).
* **Scope** — root plus the uvicorn/gunicorn loggers, all to stdout (so a
  container platform collects them).

On top of stdout logging, the **audit trail** (``AuditLogger`` /
``app/util/add_log.py``) writes structured ``Logs`` rows tagged with the
module, level, message, ``api_key``, ``oauth_user_id``, and a correlation id —
so a request can be reconstructed from the database, not just the log stream.

.. admonition:: The "Network Error" trap
   :class: warning

   A dashboard *"Network Error"* with no HTTP status is almost always a backend
   ``500`` whose body the browser dropped. The middleware ordering ensures the
   ``500`` *does* carry CORS headers; check the API logs
   (``docker logs GAME_API_DEV``) for the real traceback. See
   :doc:`architecture`.

Error tracking (Sentry)
=======================

Set ``SENTRY_DSN`` to enable Sentry. Configuration (``app/main.py``):

* ``SENTRY_ENVIRONMENT`` and ``SENTRY_RELEASE`` tag events.
* ``send_default_pii=True`` and ``traces_sample_rate=1.0`` are set; continuous
  profiling auto-starts. **Review these for your privacy/cost posture** before
  enabling in production — full-rate tracing and PII capture are convenient in
  staging but may be too much at scale.

Strategy execution traces
=========================

The domain-specific signal. Every production run of a **custom** strategy is
handled by the singleton ``DslExecutionObserver``:

#. It emits the DSL Prometheus metrics above.
#. It persists a ``StrategyExecutionLog`` row **on every error**, and on
   **successful** runs with probability ``DSL_EXECUTION_LOG_SAMPLE_RATE``
   (default ``0.05`` = 5%). Errors are always kept regardless of the rate.

A persisted row carries status, latency, node count, ``caseName``, error code,
and a **bounded** node-by-node trace (``DSL_EXECUTION_LOG_TRACE_LIMIT``,
default 200 entries; tail-truncated because the early nodes usually explain
*why* a rule matched).

Off the hot-path by design
--------------------------

The DB write does **not** block scoring. The observer enqueues the row onto a
bounded in-process queue (``DSL_EXECUTION_LOG_QUEUE_MAXSIZE``, default 1000)
drained by a background worker:

* Scoring pays only the **enqueue**, never the DB round-trip.
* If the database falls behind and the queue fills, rows are **dropped** (and
  counted by ``dsl_execution_log_dropped_total``) rather than applying
  backpressure to scoring.
* On graceful shutdown the lifespan hook **flushes** the queue
  (``observer.aclose()``) so buffered rows are not lost.

So a non-zero drop rate is an alert that the *sink* is saturated — increase the
sample budget's headroom or the queue size, or speed up the DB — but scoring
itself is never the bottleneck.

Why both metrics and traces? Metrics tell you a strategy got slow or started
erroring *in aggregate*; the sampled traces let the strategy author and the
on-call engineer look back weeks later at *which rule did what on a specific
run*, without replaying production traffic.

KPIs & operational telemetry
============================

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Source
     - Content
   * - ``KpiMetrics``
     - Daily rollups: total requests, success/error rate, average latency,
       active users, retention, average interactions per user.
   * - ``ApiRequests``
     - Per-request records (endpoint, status, response time, type).
   * - ``UptimeLogs``
     - Periodic uptime samples.

Surfaced through the dashboard and KPI endpoints:

.. code-block:: bash

   GET /api/v1/kpi/health_check
   GET /api/v1/dashboard/summary
   GET /api/v1/dashboard/summary/logs
   GET /api/v1/strategies/custom/{id}/metrics   # per-strategy aggregates
   GET /api/v1/strategies/custom/compare        # A/B comparison

What to alert on
================

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Signal
     - Why it matters
   * - ``dsl_execution_errors_total`` rising
     - A published strategy is failing — users aren't being scored as
       intended.
   * - ``dsl_execution_duration_seconds`` p99 near 500 ms
     - Strategies are approaching the wall-clock limit; some events may be
       rejected.
   * - ``dsl_execution_log_dropped_total`` > 0
     - The trace sink is saturated; you're losing audit visibility (scoring is
       fine).
   * - HTTP ``5xx`` rate
     - Backend errors; correlate with Sentry and the ``Logs`` audit trail.
