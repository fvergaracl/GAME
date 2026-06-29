===============
Getting Started
===============

.. admonition:: Who is this page for?
   :class: note

   Anyone running GAME for the first time. By the end you will have the API
   up locally and will have driven a full **game → task → points → read**
   cycle. For credentials in depth, see :doc:`authentication`.

Prerequisites
=============

.. list-table::
   :header-rows: 1
   :widths: 24 26 50

   * - Tool
     - Version
     - Notes
   * - Python
     - 3.12.x
     - Poetry constraint ``^3.12`` (effective ``>=3.12,<4.0``); CI runs 3.12.
   * - Poetry
     - latest
     - Dependency & virtualenv management.
   * - PostgreSQL
     - 14+
     - Primary datastore. Docker Compose ships one for you.
   * - Keycloak
     - 26.x *(optional)*
     - Only needed for OAuth2-protected endpoints; API-key flows work
       without it.
   * - Docker + Compose
     - latest *(optional)*
     - The fastest path to a complete local stack.

Two ways to run
===============

Path A - Docker Compose (fastest)
---------------------------------

Brings up the API, PostgreSQL, and (optionally) Keycloak together:

.. code-block:: bash

   git clone https://github.com/fvergaracl/GAME.git
   cd GAME

   # Full dev stack (API + Postgres + Keycloak)
   docker-compose -f docker-compose-dev.yml up --build

   # Tear down (and remove orphaned containers)
   docker-compose -f docker-compose-dev.yml down --remove-orphans

An "integrated" profile is also available via the ``Makefile``:

.. code-block:: bash

   make integrated   # bring up the integrated environment
   make down         # stop it

The API listens on ``http://localhost:8000``. See :doc:`operations` for the
full Compose / Kubernetes story.

Path B - Local Poetry
---------------------

Run the API directly against a PostgreSQL you provide:

.. code-block:: bash

   git clone https://github.com/fvergaracl/GAME.git
   cd GAME
   poetry install

Configure the environment from the sample and edit as needed:

.. code-block:: bash

   cp .env.sample .env

A minimal ``.env`` for local development:

.. code-block:: ini

   ENV=dev
   SECRET_KEY=change-me

   DB_ENGINE=postgresql
   DB_USER=root
   DB_PASSWORD=example
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=game_dev_db

   # Keycloak (only required for OAuth2-protected endpoints)
   KEYCLOAK_URL=http://localhost:8080
   KEYCLOAK_REALM=GameRealm
   KEYCLOAK_CLIENT_ID=game-backend
   KEYCLOAK_CLIENT_SECRET=change-me

   # DB pool tuning (recommended under concurrent load)
   SQLALCHEMY_ECHO=false
   DB_POOL_PRE_PING=true
   DB_POOL_SIZE=20
   DB_MAX_OVERFLOW=40

.. important::

   ``ENV`` gates several **fail-fast** safety checks. In ``prod``/``stage``
   the app refuses to boot if ``SECRET_KEY`` or ``KEYCLOAK_CLIENT_SECRET`` are
   missing/left at their insecure defaults, if ``DB_NAME`` is unset, or if
   ``BACKEND_CORS_ORIGINS`` is ``*``. In ``dev`` these are relaxed. Every
   variable is documented in :doc:`configuration`.

Apply the database migrations, then start the server:

.. code-block:: bash

   poetry run alembic upgrade head
   poetry run uvicorn app.main:app --reload

You now have:

* **API** → http://localhost:8000
* **Swagger UI** → http://localhost:8000/docs
* **ReDoc** → http://localhost:8000/redocs
* **Metrics** (if enabled) → http://localhost:8000/metrics

Your first end-to-end flow
==========================

This walks the canonical loop: get a credential, create a game, add a task,
award points, and read them back. It uses an **API key** (header
``X-API-Key``) - the simplest credential for server-to-server use.

1. Obtain an API key
--------------------

Creating a key is an OAuth2-protected operation, so you first need a bearer
token from Keycloak (see :doc:`authentication` for the realm setup):

.. code-block:: bash

   TOKEN=$(curl -s -X POST \
     "$KEYCLOAK_URL/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "client_id=$KEYCLOAK_CLIENT_ID" \
     -d "client_secret=$KEYCLOAK_CLIENT_SECRET" \
     -d "grant_type=password" \
     -d "username=game_admin" \
     -d "password=$KEYCLOAK_USER_WITH_ROLE_PASSWORD" | jq -r '.access_token')

   API_KEY=$(curl -s -X POST "http://localhost:8000/api/v1/apikey/create" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"client":"local-dev"}' | jq -r '.apiKey')

2. Create a game
----------------

.. code-block:: bash

   GAME_ID=$(curl -s -X POST "http://localhost:8000/api/v1/games" \
     -H "X-API-Key: $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"externalGameId":"game-001","platform":"web","strategyId":"default"}' \
     | jq -r '.gameId')

The response includes the internal ``gameId`` (a UUID). Keep it - you will
address the game by this id.

3. Create a task
----------------

.. code-block:: bash

   curl -s -X POST "http://localhost:8000/api/v1/games/$GAME_ID/tasks" \
     -H "X-API-Key: $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"externalTaskId":"task-login"}'

The task inherits the game's strategy (``default``) since it declares none of
its own.

4. Award points
---------------

.. code-block:: bash

   curl -s -X POST \
     "http://localhost:8000/api/v1/games/$GAME_ID/tasks/task-login/points" \
     -H "X-API-Key: $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"externalUserId":"user-123","data":{"event":"task_completed"}}'

Sample response::

   {
     "points": 1,
     "caseName": "BasicEngagement",
     "isACreatedUser": true,
     "gameId": "4ce32be2-...-78dc220f0520",
     "externalTaskId": "task-login",
     "created_at": "2026-02-10T12:30:00Z"
   }

``user-123`` did not exist, so GAME created it (``isACreatedUser: true``).
``caseName`` tells you *which* rule in the strategy awarded the points.

.. tip::

   To preview a score **without persisting anything**, send
   ``"isSimulated": true`` in the body. No ``UserPoints`` row, no wallet
   movement - ideal for testing a strategy. See :doc:`strategies`.

5. Read the points back
-----------------------

.. code-block:: bash

   # This user's total in this game
   curl -s "http://localhost:8000/api/v1/games/$GAME_ID/users/user-123/points" \
     -H "X-API-Key: $API_KEY"

   # The whole game, aggregated by task and user
   curl -s "http://localhost:8000/api/v1/games/$GAME_ID/points" \
     -H "X-API-Key: $API_KEY"

That is the complete loop. The :doc:`integrating` guide covers the full
catalog of game/task/points/wallet operations, and :doc:`rest-api` lists
every endpoint.

Running the tests
=================

GAME ships one-command runners (they load ``.env`` for you):

.. code-block:: bash

   # Unit tests
   ./scripts/run_unit_tests.sh
   ./scripts/run_unit_tests.sh --cov --cov-branch --cov-report html

   # End-to-end (isolated SQLite, deterministic, no real infra)
   ./scripts/run_e2e.sh
   # …plus real HTTP + PostgreSQL + Keycloak
   ./scripts/run_e2e.sh --real

   # Load tests (k6)
   ./scripts/run_load_test.sh --mode 100

See :doc:`contributing` for the testing strategy and ``--help`` on each
runner for the full option set.

Troubleshooting first run
=========================

.. list-table::
   :header-rows: 1
   :widths: 38 62

   * - Symptom
     - Likely cause / fix
   * - App won't boot in ``prod``/``stage``
     - A fail-fast secret check tripped. The error names the missing variable
       (``SECRET_KEY``, ``KEYCLOAK_CLIENT_SECRET``, ``DB_NAME``). See
       :doc:`configuration`.
   * - ``401 Invalid authentication credentials``
     - No/!invalid ``X-API-Key`` and no valid bearer token. See
       :doc:`authentication`.
   * - Dashboard shows "Network Error"
     - Usually a backend ``500`` whose body CORS dropped. Check API logs for
       the real traceback (see :doc:`architecture`).
   * - ``404`` on a freshly created game
     - You addressed it with your ``externalGameId`` instead of the returned
       internal ``gameId``. See :doc:`domain-model`.
