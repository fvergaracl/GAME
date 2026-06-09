==========
Operations
==========

.. admonition:: Who is this page for?
   :class: note

   Operators deploying and running GAME. Pairs with :doc:`configuration`
   (every variable), :doc:`security` (hardening), and :doc:`observability`
   (signals). The repository also keeps ``DEPLOYMENT.md`` and
   ``KUBERNETES_SETUP.md`` as quick references.

Deployment topology
===================

GAME is **stateless**: it holds no per-request server state beyond the
database (and optional Redis). That means you scale it by running more
identical replicas behind a load balancer; PostgreSQL and Redis are the only
shared state.

::

   ┌────────────┐     ┌──────────────┐     ┌──────────────┐
   │  Ingress / │────►│  GAME API    │────►│  PostgreSQL  │
   │  Load bal. │     │  (N replicas)│     └──────────────┘
   └────────────┘     │  gunicorn +  │────►┌──────────────┐
        │             │  uvicorn     │     │   Redis      │ (optional:
        │             └──────┬───────┘     └──────────────┘  rate-limit +
        ▼                    │                                apikey cache)
   ┌────────────┐            ▼
   │  Keycloak  │◄───── JWT validation (JWKS)
   └────────────┘

The process model in containers is **gunicorn** managing **uvicorn** workers
(``app/gunicorn_conf.py``, ``app/start-prod.sh``).

Local & dev with Docker Compose
===============================

The repository ships several Compose files and a ``Makefile`` that wraps them
(auto-detecting ``docker compose`` v2 vs ``docker-compose`` v1):

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Make target
     - What it does
   * - ``make setup``
     - First-run: installs Docker if missing, creates ``.env`` from the
       sample (interactive).
   * - ``make dev``
     - Dev stack (``docker-compose-dev.yml``): API + Postgres + Keycloak.
   * - ``make dev-nodb``
     - Dev stack without a bundled DB (bring your own).
   * - ``make integrated``
     - Integrated stack (``docker-compose.devintegrated.yml``).
   * - ``make up`` / ``make up-fg``
     - Start in background / foreground.
   * - ``make logs`` / ``make logs-api``
     - Tail logs (all services / just the API).
   * - ``make ps``
     - Show running containers.
   * - ``make shell-api`` / ``make shell-db``
     - Shell into the API container / ``psql`` into Postgres.
   * - ``make down`` / ``make clean``
     - Stop+remove containers / …**and volumes** (destructive).
   * - ``make audit``
     - Run ``pip-audit`` locally (parity with CI).

Override the compose file or command per invocation, e.g.
``make up FILE=docker-compose.yml DC="docker-compose"``.

Raw Compose, without Make:

.. code-block:: bash

   # Dev
   docker-compose -f docker-compose-dev.yml up --build
   docker-compose -f docker-compose-dev.yml down --remove-orphans

   # Production-style single host
   docker-compose up --build -d
   docker-compose logs -f
   docker-compose up --scale app=3      # horizontal scale

Production deployment
=====================

#. **Configure** the environment for ``ENV=prod`` (or ``stage``). The
   fail-fast guards will block boot on missing secrets — that is intended; see
   :doc:`configuration` and :doc:`security`.
#. **Run migrations** before serving traffic (see below).
#. **Deploy** the image with your orchestrator (Compose, Kubernetes, or a
   managed container platform), behind an ingress that terminates TLS.
#. **Set ``TRUSTED_PROXY_IPS``** to the ingress IP/CIDR so per-IP rate limits
   work and forwarding headers are trusted.
#. **Protect ``/metrics``** at the ingress, or set ``METRICS_ENABLED=false``.
#. **Externalize shared state**: point ``REDIS_URL`` and switch
   ``ABUSE_PREVENTION_BACKEND`` / ``APIKEY_CACHE_BACKEND`` to ``redis`` so
   limits and key revocations are consistent across replicas.

Kubernetes
==========

Manifests live under ``kubernetes/`` and a helper script
``deploy-kubernetes.sh`` is provided. See ``KUBERNETES_SETUP.md`` for the full
walkthrough. Operational notes:

* Define **liveness/readiness probes** — ``GET /api/v1/kpi/health_check`` is a
  natural readiness target.
* Provide configuration via ``ConfigMap`` (non-secret) and ``Secret``
  (``SECRET_KEY``, DB password, ``KEYCLOAK_CLIENT_SECRET``).
* Roll back with ``kubectl rollout undo deployment/<name>`` — Kubernetes keeps
  the deployment history.

Database migrations (Alembic)
=============================

Schema changes are Alembic migrations (``migrations/``, ``alembic.ini``). The
golden rule: **migrate before the new code serves traffic**, in CI/CD.

.. code-block:: bash

   # Local / Poetry
   poetry run alembic upgrade head

   # Inside a running container
   docker-compose exec app alembic upgrade head

   # Generate a new migration after a model change (review before committing!)
   poetry run alembic revision --autogenerate -m "describe change"

Health, readiness & graceful shutdown
=====================================

* **Health** — ``GET /api/v1/kpi/health_check``.
* **Graceful shutdown** — the FastAPI lifespan hook flushes the DSL
  execution-log queue on shutdown (``observer.aclose()``) so buffered audit
  rows aren't lost. Give the container a few seconds of termination grace so
  the flush completes.

Scaling guidance
================

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Lever
     - Guidance
   * - **Replicas / workers**
     - Scale horizontally; the app is stateless. Size gunicorn workers to CPU.
   * - **DB pool**
     - Total connections ≈ replicas × workers × (``DB_POOL_SIZE`` +
       ``DB_MAX_OVERFLOW``). Keep it under PostgreSQL's ``max_connections``;
       consider PgBouncer at high replica counts.
   * - **Rate-limit & cache backend**
     - Use ``redis`` so limits and key revocations are global, not per-worker.
   * - **DSL trace sink**
     - Watch ``dsl_execution_log_dropped_total``; if non-zero, the trace DB is
       behind — raise ``DSL_EXECUTION_LOG_QUEUE_MAXSIZE`` or lower the sample
       rate. Scoring is unaffected (:doc:`observability`).

Load & performance testing
==========================

A k6 load suite ships in ``tests/load`` with a runner:

.. code-block:: bash

   ./scripts/run_load_test.sh --mode 100        # 100 VUs
   ./scripts/run_load_test.sh --mode 1000       # stress
   ./scripts/run_load_test.sh --vus 300 \
     --mix-a 60 --mix-b 30 --mix-c 10 \
     --warmup 20s --hold 2m --ramp-down 20s

See :doc:`contributing` for the full testing story and the README for every
flag.

Runbooks
========

* **DSL strategy incidents** (a published strategy erroring, hitting limits,
  or needing rollback) → ``docs/dsl/runbook.md`` and :doc:`strategies`.
* **"Network Error" in the dashboard** → almost always a backend ``500``;
  check API logs (:doc:`observability`).
* **Boot failure in prod/stage** → a fail-fast guard tripped; the error names
  the variable (:doc:`configuration`).
