=======================
The DSL Strategy Engine
=======================

.. admonition:: Who is this page for?
   :class: note

   Contributors and security reviewers who need to understand how custom
   strategies execute safely. Strategy *authors* want :doc:`strategies` and
   the per-block reference under ``docs/dsl/``.

Why a DSL at all?
=================

Custom scoring logic is **user-supplied** - authored in a browser by people
who are not GAME developers. Running arbitrary user code on the scoring
hot-path is a non-starter, so GAME defines a small, total, sandboxed
**domain-specific language**. A strategy is a JSON **AST** (abstract syntax
tree) of typed *blocks*; the engine interprets that tree. There is no Python
generated, compiled, or executed.

The pipeline
============

A custom strategy travels through four stages::

   Blockly editor ──► JSON AST ──► validate_ast() ──► persist (StrategyDefinition)
                                                            │
   scoring event ──► ExecutionContext.build_for_ast ──► DslInterpreter.execute ──► (points, caseName, callbackData)

1. Validation (``dsl_validator.py``)
------------------------------------

Runs synchronously, with **no I/O**, on every create/update (and again, cheaply,
before each simulation). It enforces three things in order:

#. **Shape** - every node has the required keys with the expected types (a
   rule has a ``when``; a literal is a scalar, not a dict).
#. **Whitelist** - ``node.type``, ``compare.op``, ``arith.op``, and
   ``field.path`` must each appear in the corresponding allow-list in
   ``dsl_ast``. Unknown names are rejected here, before they can reach the
   interpreter.
#. **Limits** - a *static* node count and recursion depth are computed during
   the walk and bounded by ``DSL_MAX_NODES`` / ``DSL_MAX_DEPTH``, so a
   billion-node tree can never be persisted, let alone executed.

The validator also fills in missing node ``id`` fields with a deterministic
``"<parent_id>.<type>.<index>"`` slug, giving every node a stable correlation
key for traces and error messages.

2. Context building (``dsl_execution_context.py``)
--------------------------------------------------

Before a walk, ``ExecutionContext.build_for_ast`` **precomputes** every
analytics value the AST references (the ``field`` paths) into a frozen
dictionary. The interpreter then does pure dictionary lookups - it never
reaches back into the database or computes analytics mid-walk. This is what
keeps execution bounded and deterministic.

3. Interpretation (``dsl_interpreter.py``)
------------------------------------------

The interpreter **is the sandbox**. It walks the AST node-by-node, dispatching
on ``node["type"]`` through a **fixed handler table**. Its hard guarantees:

* **No dynamic Python** - no ``eval``, no ``exec``, no ``getattr`` on
  AST-supplied strings. A node type absent from the handler table is rejected
  as ``DslValidationError`` (defence in depth - the validator should already
  have caught it).
* **Frozen field access** - reading a ``field`` is a lookup in the precomputed
  frozen dict; AST strings can never address arbitrary attributes.
* **Bounded** - node count and recursion depth are re-checked at runtime, so
  even a future feature like macros couldn't blow the limits.
* **Actually cancellable** - the walk ``await asyncio.sleep(0)`` every
  ``yield_every`` (default **64**) node visits. Without that yield a CPU-bound
  tree would run to completion and *then* notice the timeout; the yield lets
  ``asyncio.wait_for`` cancel it mid-walk. (This is the failure mode that
  ``RestrictedPython``-style sandboxes usually get wrong.)

Execution semantics mirror the built-in ``default`` strategy:

* Rules evaluate **in order**.
* The **first** ``assign_points`` reached inside a matched rule sets the result
  and **halts** (early return). ``set_callback_data`` statements *before* the
  assignment accumulate into a dict; statements *after* it never run.
* If no rule matches, the program's ``default`` section runs; otherwise the
  result is ``(0, None, {})``.

Execution modes
===============

``DslInterpreter.execute`` takes a ``mode`` selecting which section runs. This
is how ``DSL_EXTEND`` strategies wrap a built-in parent (orchestrated by
``DslStrategy``):

.. list-table::
   :header-rows: 1
   :widths: 14 86

   * - Mode
     - Behavior
   * - ``full``
     - Main ``rules`` + ``default`` - the ``DSL_FULL`` path.
   * - ``pre``
     - Only ``pre_rules``. ``initial_data`` is cloned into
       ``working_data`` so ``set_data`` can mutate the input the parent will
       see; a ``veto`` here signals the orchestrator to skip the parent and
       all post-rules.
   * - ``post``
     - Only ``post_rules``. The parent built-in's output bootstraps the run
       state, so ``set_points`` / ``set_case_name`` / ``set_callback_data``
       mutate *from* the parent's result. The ``parent.points`` /
       ``parent.case_name`` field paths are pre-resolved into the context.

The result is a ``DslExecutionResult`` carrying ``points``, ``case_name``,
``callback_data``, an optional ``trace`` (node-by-node), and the
``DSL_EXTEND`` signals ``working_data`` and ``vetoed``.

Limits & error taxonomy
=======================

.. list-table::
   :header-rows: 1
   :widths: 30 16 54

   * - Guard
     - Default
     - Effect on breach
   * - ``DSL_EXECUTION_TIMEOUT_MS``
     - 500 ms
     - Wall-clock backstop; the cooperative yield lets the walk be cancelled.
   * - ``DSL_MAX_NODES``
     - 1000
     - Rejected at validation; re-checked at runtime.
   * - ``DSL_MAX_DEPTH``
     - 32
     - Rejected at validation; re-checked at runtime.

Errors are typed (``app/core/exceptions``):

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Exception
     - Raised when
   * - ``DslValidationError``
     - The AST is structurally invalid or references a non-whitelisted
       name/op/field. Surfaced at create/update time.
   * - ``DslLimitExceededError``
     - Node/depth/time limits are exceeded.
   * - ``DslExecutionError``
     - A runtime error inside an otherwise valid program (e.g. a disallowed
       operation slipped through).

See the operational ``docs/dsl/runbook.md`` for what to do when these fire in
production.

Built-in strategies in code
===========================

Built-ins are ordinary Python (not DSL). They:

#. subclass ``BaseStrategy`` (``app/engine/base_strategy.py``),
#. implement the async ``calculate_points`` scoring method, and
#. register a **stable public id** with ``@register_strategy(id=...)``.

``BaseStrategy`` also computes a ``hash_version`` - a SHA-256 of the
``calculate_points`` source - so a logic change is detectable as a version
change. The registry (``strategy_registry.py``) is explicit and
opt-in; ``all_engine_strategies.py`` discovers modules in ``app/engine`` via
``pkgutil`` (CWD-independent), and **external packages** can contribute
strategies through the ``game.strategies`` entry-point group without forking.

Observability hooks
===================

Every production DSL run is observed by the singleton ``DslExecutionObserver``
(wired in the container). It:

* emits Prometheus counters/histograms (``dsl_execution_duration_seconds``,
  ``dsl_execution_nodes_total``, ``dsl_execution_errors_total``), and
* persists a ``StrategyExecutionLog`` row on **every error**, and on
  **successful** runs with probability ``DSL_EXECUTION_LOG_SAMPLE_RATE``
  (default 5%).

The DB write is drained off the hot-path by a background worker fed from a
bounded in-process queue, so scoring only pays the enqueue. The full model -
queue sizing, drop counting, graceful flush on shutdown - is in
:doc:`observability`.

Source map
==========

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Module
     - Responsibility
   * - ``app/engine/dsl_ast.py``
     - Node-type constants and the operator/function/field allow-lists.
   * - ``app/engine/dsl_validator.py``
     - Structural + whitelist + limit validation.
   * - ``app/engine/dsl_execution_context.py``
     - Precomputes analytics fields into a frozen lookup table.
   * - ``app/engine/dsl_interpreter.py``
     - The sandboxed walker.
   * - ``app/engine/dsl_strategy.py``
     - Orchestrates ``DSL_EXTEND`` (pre → parent → post).
   * - ``app/engine/dsl_metrics.py``
     - Prometheus metric definitions.
   * - ``app/engine/base_strategy.py`` / ``strategy_registry.py``
     - Built-in strategy base class and the explicit registry.

The auto-generated reference for these modules is in :doc:`codebase`.
