============
Contributing
============

.. admonition:: Who is this page for?
   :class: note

   Developers changing GAME's code or docs. The repository's ``CONTRIBUTING.md``
   and ``TESTING.md`` are the canonical quick references; this page adds the
   architectural and documentation context.

Development setup
=================

.. code-block:: bash

   git clone https://github.com/fvergaracl/GAME.git
   cd GAME
   poetry install
   cp .env.sample .env
   poetry run alembic upgrade head
   poetry run uvicorn app.main:app --reload   # http://localhost:8000

Read :doc:`architecture` before your first non-trivial change — the layer
boundaries are enforced socially, not by the compiler, so knowing *which layer
owns what* is how reviews go smoothly.

Where code goes
===============

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Change
     - Lives in
   * - New HTTP endpoint
     - ``app/api/v1/endpoints/`` + register the router in
       ``app/api/v1/routes.py``.
   * - Business logic
     - ``app/services/`` — never put it in an endpoint or repository.
   * - New persistence query
     - ``app/repository/`` — keep it free of domain decisions.
   * - New table
     - ``app/model/`` + an Alembic migration in ``migrations/``.
   * - Wire-format change
     - ``app/schema/`` (Pydantic).
   * - New scoring strategy
     - ``app/engine/`` — subclass ``BaseStrategy`` and decorate with
       ``@register_strategy(id=...)``.
   * - New dependency wiring
     - ``app/core/container.py``.

Testing
=======

GAME uses ``pytest`` with a layered suite under ``tests/`` and one-command
runners (they load ``.env`` for you):

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Suite
     - Run it
   * - **Unit**
     - ``./scripts/run_unit_tests.sh`` (``--fail-fast``, ``--cov``,
       ``--file <path>``). Fast, isolated, mock external dependencies.
   * - **E2E (controlled)**
     - ``./scripts/run_e2e.sh`` — isolated SQLite, deterministic, no real
       infra.
   * - **E2E (real infra)**
     - ``./scripts/run_e2e.sh --real`` — real HTTP + PostgreSQL + Keycloak.
   * - **Load (k6)**
     - ``./scripts/run_load_test.sh --mode 100``.

Or drive ``pytest`` directly:

.. code-block:: bash

   poetry run pytest
   poetry run pytest --cov=app --cov-branch --cov-report=html
   poetry run pytest -k "test_assign_points"

Guidelines:

* Every feature/fix ships with tests. Unit-test services in isolation;
  reserve real-infra E2E for integration behavior.
* Because persistence is abstracted, services run against **SQLite** in tests
  and **PostgreSQL** in production — keep repository queries portable.
* CI runs the suite with coverage; Codecov tracks the trend.

Code style
==========

* **Python 3.12**, PEP 8. Formatting/linting is handled by **Ruff**
  (``ruff_cache`` is present); run it before pushing.
* Public functions and classes get **Google-style docstrings** — they are not
  decoration, they *are* the API reference (:doc:`codebase`) via ``napoleon``.
* Match the surrounding code: the codebase favors small, well-named functions,
  explicit dependencies, and comments that explain *why* (often referencing the
  sprint or the bug a guard prevents) rather than *what*.

Documentation
=============

Docs are part of the product, not an afterthought. The information
architecture follows the `Diátaxis <https://diataxis.fr/>`_ model — every page
declares *who it is for* and stays in its lane:

.. list-table::
   :header-rows: 1
   :widths: 22 38 40

   * - Diátaxis type
     - Purpose
     - Examples here
   * - Tutorial
     - Learning by doing
     - :doc:`getting-started`
   * - How-to
     - Task-oriented steps
     - :doc:`integrating`, :doc:`operations`
   * - Explanation
     - Understanding
     - :doc:`overview`, :doc:`architecture`, :doc:`dsl-engine`
   * - Reference
     - Dry facts
     - :doc:`configuration`, :doc:`rest-api`, :doc:`codebase`

Where docs live
---------------

.. list-table::
   :header-rows: 1
   :widths: 36 64

   * - Location
     - Content
   * - ``docs/source/*.rst``
     - This Sphinx site (reStructuredText). Built to GitHub Pages on every
       push to ``main``.
   * - ``docs/source/api/``
     - Auto-generated module reference (``sphinx-apidoc`` + ``autodoc``).
   * - ``docs/dsl/``
     - DSL block reference and runbook (linked from the editor).
   * - ``docs/domain-model.md``
     - Canonical Mermaid ERD.
   * - Top-level ``*.md``
     - ``README``, ``SETUP``, ``DEPLOYMENT``, ``TESTING``, ``KUBERNETES_SETUP``
       — entry points and quick references.

Building the docs locally
-------------------------

.. code-block:: bash

   # One-off build
   poetry run sphinx-build -b html docs/source _build/html

   # Live-reloading preview while you write
   poetry run sphinx-autobuild docs/source _build/html

   # Regenerate the module reference after adding/moving modules
   .venv/bin/sphinx-apidoc -f -e -M -o docs/source/api app

Keep the build **warning-clean**: a broken cross-reference or an orphaned page
is a bug. Add a one-line *"Who is this page for?"* admonition to every new
page so its audience is explicit.

Submitting a change
===================

#. Branch: ``git checkout -b feature/your-feature-name``.
#. Make the change *with* tests and docstrings/docs.
#. Run the relevant test suite and the docs build locally.
#. Open a PR with a clear description and linked issues. CI runs tests,
   coverage, linting, ``pip-audit`` (``make audit`` locally), and the docs
   build.

Report bugs and request features via `GitHub Issues
<https://github.com/fvergaracl/GAME/issues>`_; discuss design in `GitHub
Discussions <https://github.com/fvergaracl/GAME/discussions>`_.
