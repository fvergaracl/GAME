:og:description: GAME (Goals And Motivation Engine) - an adaptive,
   programmable gamification engine for shaping participation and incentives.

==================================
GAME - Goals And Motivation Engine
==================================

.. rubric:: An adaptive, programmable gamification engine

**GAME** turns user activity into points, coins, and behavioral incentives
through *programmable scoring strategies*. Unlike static points APIs whose
rules are frozen at design time, GAME lets a strategy react to behavior,
context, and system state - so incentives can be **redistributed** toward
under-engaged users, tasks, or regions instead of amplifying the
participation inequality that fixed rules tend to reinforce.

It runs in two shapes:

* as a **complete gamification backend** - manage games, tasks, users,
  point assignment, and wallets; or
* as a **scoring microservice** - your system owns the application logic
  and calls GAME only to compute *how many points* an event is worth.

----

.. admonition:: New here? Start with the path that matches your goal
   :class: tip

   This documentation follows the `Diátaxis <https://diataxis.fr/>`_ model -
   it separates *learning-oriented* tutorials, *task-oriented* how-to guides,
   *understanding-oriented* explanation, and dry *reference*. Pick your lane:

   * **I want to call the API in 5 minutes** →
     :doc:`getting-started` then :doc:`authentication`.
   * **I want to integrate GAME into my product** →
     :doc:`integrating` and :doc:`strategies`.
   * **I want to understand how it works** →
     :doc:`overview`, :doc:`architecture`, :doc:`dsl-engine`.
   * **I run it in production** →
     :doc:`configuration`, :doc:`operations`, :doc:`observability`,
     :doc:`security`.
   * **I'm contributing code** →
     :doc:`architecture`, :doc:`codebase`, :doc:`contributing`.

Audience map
============

This site serves two readers at once, and every page declares which one it
is written for:

.. list-table::
   :header-rows: 1
   :widths: 22 38 40

   * - Reader
     - You want to…
     - Read first
   * - **Integrator**
     - Consume GAME from an external app as a gamification/scoring backend.
     - :doc:`getting-started`, :doc:`authentication`, :doc:`integrating`,
       :doc:`strategies`, :doc:`rest-api`
   * - **Contributor / Operator**
     - Extend the engine, run it, or reason about its internals.
     - :doc:`architecture`, :doc:`dsl-engine`, :doc:`security`,
       :doc:`observability`, :doc:`configuration`, :doc:`operations`

----

.. toctree::
   :maxdepth: 2
   :caption: Overview & Concepts

   overview
   architecture
   domain-model

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting-started
   authentication

.. toctree::
   :maxdepth: 2
   :caption: Integration Guides

   integrating
   strategies

.. toctree::
   :maxdepth: 2
   :caption: Engine Internals (Contributors)

   dsl-engine
   security
   observability

.. toctree::
   :maxdepth: 2
   :caption: Operations

   configuration
   operations

.. toctree::
   :maxdepth: 2
   :caption: Reference

   rest-api
   codebase
   contributing

----

At a glance
===========

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Property
     - Value
   * - Stack
     - Python ≥ 3.12 · FastAPI/Starlette · SQLModel/SQLAlchemy 2.0 (async) ·
       PostgreSQL · Keycloak (OIDC) · Redis (optional)
   * - Architecture
     - Layered - *endpoint → service → strategy engine → repository →
       database* - wired by a dependency-injection container
   * - Scoring
     - Built-in deterministic & adaptive strategies, plus a sandboxed
       **DSL** (no-code, Blockly-authored) with hard CPU/size limits
   * - Auth
     - API key (``X-API-Key``) **or** OAuth2 bearer (Keycloak), with
       per-key scoping and rate limiting
   * - Observability
     - Prometheus ``/metrics``, structured JSON logs, Sentry, sampled DSL
       execution traces, KPI rollups
   * - Reproducibility
     - Deterministic execution, simulation mode (``isSimulated``),
       versionable strategies - usable as an experimental research platform

----

.. seealso::

   * **Interactive API** - every deployment serves Swagger UI at ``/docs``
     and ReDoc at ``/redocs`` generated from the live OpenAPI schema.
   * **Roadmap** - what is stable, experimental, and planned:
     `ROADMAP.md <https://github.com/fvergaracl/GAME/blob/main/ROADMAP.md>`_
   * **Source** - https://github.com/fvergaracl/GAME
   * **License** - Apache-2.0
