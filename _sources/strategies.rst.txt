==========
Strategies
==========

.. admonition:: Who is this page for?
   :class: note

   Integrators and strategy authors who decide *how many* points an event is
   worth. This is the conceptual + how-to view. The interpreter internals
   (AST, limits, sandbox) are in :doc:`dsl-engine`; the per-block editor
   reference lives under ``docs/dsl/``.

.. admonition:: Which strategy model should I use?
   :class: important

   GAME has **two ways to author a strategy**, aimed at different people:

   * **Built-in classes (Python).** Subclasses of ``BaseStrategy`` registered
     in the engine. This is the **stable, recommended path for engineers** who
     can ship code; ``default`` is the safe baseline. See
     `Built-in strategies`_ and `The Python scoring contract`_ below.
   * **The DSL (no-code).** Strategies authored visually in the dashboard and
     stored as ``custom:<uuid>``, executed in a sandbox. This is the
     **no-code path for designers**: production-usable but newer, and its
     scoring semantics mirror the ``default`` built-in. See
     `Custom strategies (the DSL)`_ below.

   Rule of thumb: reach for a **built-in class** when the logic is complex,
   performance-critical, or ships with the codebase; reach for the **DSL**
   when a non-engineer needs to tune scoring without a deploy. Both run through
   the same engine and are deterministic given identical inputs.

What a strategy is
==================

A **strategy** is the scoring brain bound to a game (and optionally overridden
per task). When an event arrives, GAME resolves the effective strategy and
asks it for two things:

* ``points`` - the integer reward, and
* ``caseName`` - the human-readable label for *why* that amount was chosen
  (e.g. ``BasicEngagement``, ``PeakPerformerBonus``). The ``caseName``
  flows into responses, analytics, and audit so a decision is always
  explainable.

Strategies come in two families:

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Family
     - Behavior
   * - **Deterministic**
     - Fixed, rule-based scoring. Same event → same points, always.
   * - **Adaptive**
     - Scoring reacts to context: the user's history, the task's distribution,
       comparison to the global average, spatial state, etc.

Both families are **deterministic given identical inputs** - adaptivity means
the inputs include behavioral/contextual analytics, not that the output is
random. That is what makes GAME reproducible (see :doc:`overview`).

Choosing a strategy: ``strategyId``
===================================

Every game stores a ``strategyId``; tasks inherit it unless they set their
own. Two id shapes exist:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shape
     - Meaning
   * - ``<builtin-id>``
     - A code-defined strategy registered in the engine (table below).
   * - ``custom:<uuid>``
     - A DSL strategy authored in the dashboard and stored in the database.

If no strategy is set, the built-in ``default`` applies.

Built-in strategies
===================

These ship with the engine. Each registers a **stable public id** (persisted
on games and returned by the API) via ``@register_strategy`` - the id is
guaranteed stable across class renames:

.. list-table::
   :header-rows: 1
   :widths: 26 12 62

   * - ``strategyId``
     - Version
     - Purpose
   * - ``default``
     - 0.0.2
     - The baseline. Awards configurable basic/bonus points; the safe default
       for any game.
   * - ``constantEffortStrategy``
     - 0.0.1
     - Rewards steady, sustained participation rather than bursts.
   * - ``socio_bee``
     - 0.0.2
     - Tuned for the SOCIO-BEE citizen-science scenario.
   * - ``greencrowdStrategy``
     - 1.0.0
     - Tuned for the GREENCROWD platform.
   * - ``greengageStrategy``
     - 0.0.1
     - Tuned for the GREENGAGE scenario.
   * - ``getis_ord_gi_star``
     - 0.0.1
     - **Spatial, experimental.** The Getis-Ord :math:`G_i^*` hot-spot
       computation works standalone, but the strategy is **not yet wired
       into scoring**: ``GetisOrdStrategy`` does not subclass
       ``BaseStrategy`` and its ``calculate_points`` is still a stub. Not
       production-ready.

Discover them at runtime:

.. code-block:: bash

   GET /api/v1/strategies                 # list available strategies
   GET /api/v1/strategies/{id}            # one strategy's metadata
   GET /api/v1/strategies/{id}/schema     # its configurable variables
   GET /api/v1/strategies/{id}/graph      # a rendered logic graph

Strategy **variables** (e.g. ``variable_basic_points``) are the knobs;
game/task **params** supply their values, so the same strategy behaves
differently per game without code changes.

.. admonition:: Extending the engine in code
   :class: tip

   New built-ins are plain classes that subclass ``BaseStrategy``, implement
   the scoring method, and decorate themselves with
   ``@register_strategy(id="...")``. Third-party packages can even contribute
   strategies through the ``game.strategies`` entry-point group - no fork
   required. See :doc:`dsl-engine` and :doc:`codebase`.

The Python scoring contract
===========================

A built-in is a class that subclasses ``BaseStrategy``, registers a stable id,
and implements one coroutine. The signature is the same one ``BaseStrategy``
declares, so subclasses inherit it without surprises:

.. code-block:: python

   from app.engine.base_strategy import BaseStrategy
   from app.engine.strategy_registry import register_strategy


   @register_strategy(id="streak_bonus", version="0.0.1")
   class StreakBonusStrategy(BaseStrategy):
       async def calculate_points(
           self, externalGameId, externalTaskId, externalUserId, data=None
       ):
           # Return (points, caseName): the reward and why it was chosen.
           if (data or {}).get("streak", 0) >= 5:
               return (10, "StreakBonus")
           return (1, "BasicEngagement")

``calculate_points`` returns a ``(points, caseName)`` tuple - ``points`` is the
integer reward and ``caseName`` is the label explaining *why* that amount was
chosen (it flows into responses, analytics, and audit). A strategy may return
an optional third element, ``callbackData``, to pass structured data back to
the caller. The bundled ``default`` strategy
(``app/engine/default.py``) is the reference implementation of this contract.

Custom strategies (the DSL)
===========================

The dashboard's **Strategy Editor** lets game designers build strategies
visually (Blockly) with **no Python**. A strategy is a tree of *blocks*; when
a scoring event arrives the engine walks the tree top-to-bottom and emits the
first ``assign_points`` it reaches inside a matching rule.

Authoring modes
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Mode
     - What you do
   * - ``DSL_FULL``
     - Write the whole strategy from scratch: a top-down list of ``rules``
       (first match wins) plus a ``default`` fallback.
   * - ``DSL_EXTEND``
     - Start from a built-in (e.g. ``default``) and layer ``pre_rules`` (may
       mutate the input or *veto* the award) and ``post_rules`` (may multiply
       points, override the case name, or add callback data), with optional
       per-realm ``parent_variables`` overrides.

Templates give authors a running start - both engine templates
(``default``, ``constant_effort``) and ready-made examples such as
*engagement_basico*, *recompensa_completar_tarea*, *bonus_por_velocidad*, and
*bonus_extiende_default*:

.. code-block:: bash

   GET /api/v1/strategies/custom/templates

The custom-strategy lifecycle
=============================

Custom strategies are first-class, **versioned** resources:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Operation
     - Endpoint
   * - Create a draft
     - ``POST /strategies/custom``
   * - List / get
     - ``GET /strategies/custom``, ``GET /strategies/custom/{id}``
   * - Update (creates a new draft of a published strategy)
     - ``PUT /strategies/custom/{id}``
   * - Publish a version
     - ``POST /strategies/custom/{id}/publish``
   * - Archive
     - ``POST /strategies/custom/{id}/archive``
   * - List versions
     - ``GET /strategies/custom/{id}/versions``
   * - Roll back to a version
     - ``POST /strategies/custom/{id}/rollback/{version}``
   * - Where is it used?
     - ``GET /strategies/custom/{id}/usage``
   * - Import / export
     - ``POST /strategies/custom/import``
   * - Simulate (no persistence)
     - ``POST /strategies/custom/simulate``,
       ``POST /strategies/custom/{id}/simulate``

Versioning guarantees
---------------------

* Saving a **published** strategy creates a ``v+1`` **draft** rather than
  overwriting. Production keeps running the published version until you
  explicitly publish the new one.
* If a published version misbehaves, **rollback** restores a prior version.
  Rollback also rewrites the ``strategyId`` on every game/task that pointed at
  the archived version, so the cascade reaches all consumers.

This means you can experiment freely - nothing in production changes until you
press *Publish*.

Simulate before you ship
========================

Every strategy can be **simulated**: scoring runs and you get the full
node-by-node trace, but **no production data is touched** - no ``UserPoints``,
no wallet movement.

Two ways to simulate:

* **Per-event** - send ``"isSimulated": true`` to the points endpoint
  (:doc:`integrating`).
* **Per-strategy** - call ``POST /strategies/custom/{id}/simulate`` (the
  editor's *Test* button) to dry-run a candidate strategy against sample
  input and inspect exactly which rule would fire and why.

There is also a per-user simulated view,
``GET /games/{gameId}/users/{externalUserId}/points/simulated`` (OAuth2-only,
bound to the caller's own subject), returning a ``simulationHash`` for
integrity plus per-task projected points.

Use simulation liberally - it is the safe way to validate a scoring change.

Safety limits
=============

Published DSL strategies run inside a sandbox with hard ceilings so a runaway
rule cannot impact your tenant or others:

.. list-table::
   :header-rows: 1
   :widths: 38 18 44

   * - Limit
     - Default
     - Env var
   * - Wall-clock per call
     - 500 ms
     - ``DSL_EXECUTION_TIMEOUT_MS``
   * - AST nodes visited
     - 1000
     - ``DSL_MAX_NODES``
   * - Recursion depth
     - 32
     - ``DSL_MAX_DEPTH``

Hitting a limit rejects the event with a clear error code rather than
degrading the service. The full execution model - how the interpreter yields
cooperatively so the timeout can actually cancel it - is in :doc:`dsl-engine`.

Worked example: adaptive engagement
===================================

A common pattern (from the citizen-science deployments) layers cases by the
user's measurement count and performance. The ``caseName`` values below are
the labels *you* assign when authoring the strategy in the DSL - illustrative,
not a literal dump of the bundled ``default`` built-in's outputs:

.. list-table::
   :header-rows: 1
   :widths: 28 30 42

   * - Case
     - Condition
     - ``caseName``
   * - First/second measurement
     - No prior history
     - ``BasicEngagement``
   * - Slower than global avg
     - ``time > global``
     - ``PerformancePenalty``
   * - Faster than global avg
     - ``time < global``
     - ``PerformanceBonus``
   * - Beats own history *and* global
     - ``time < individual && time < global``
     - ``PeakPerformerBonus``

The full decision tree and points table is in the repository's
``strategies.md``; expressing it in the editor is a matter of nesting
``gd_rule`` blocks with ``gd_compare`` conditions and ``gd_assign_points``
leaves.

Observability
=============

Every production run of a custom strategy emits Prometheus metrics
(``dsl_execution_duration_seconds``, ``dsl_execution_nodes_total``,
``dsl_execution_errors_total``) and, on failure or by sampling, persists a
``StrategyExecutionLog`` row you can inspect later. Aggregations are available
at ``GET /strategies/custom/{id}/metrics`` and an A/B view at
``GET /strategies/custom/compare``. See :doc:`observability`.
