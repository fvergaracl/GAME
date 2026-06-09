========
Overview
========

.. admonition:: Who is this page for?
   :class: note

   Everyone. It explains *what* GAME is, *what problem* it solves, and the
   vocabulary used throughout the rest of the documentation. No code.

What is GAME?
=============

**GAME (Goals And Motivation Engine)** is an *adaptive gamification engine*.
It accepts events - "a user completed a task", "a measurement was submitted" -
and decides how many **points** to award, why, and what side effects follow
(coins, wallet movements, callbacks). The decision is made by a **strategy**:
a unit of scoring logic bound to a game or an individual task.

The defining idea is that strategies are **programmable and adaptive**. A
strategy is not limited to "task X is worth N points". It can read analytics
about the user and the task - how many times the user has acted, how their
completion time compares to their own history or to the global average - and
shape the reward accordingly.

The problem GAME solves
=======================

Most gamification systems are **static**: rules and rewards are fixed at
design time. Static rules produce predictable engagement curves and, in
practice, tend to *reinforce participation inequality* - the users who are
already active collect most of the rewards, while under-engaged users see no
reason to start.

GAME introduces **adaptive gamification**, enabling:

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Capability
     - What it means
   * - **Adaptive vs. static**
     - Scoring rules can react to behavior, context, or system state instead
       of being frozen constants.
   * - **Behavioral redistribution**
     - Incentives can shift participation toward under-engaged users, tasks,
       or areas.
   * - **Incentive shaping**
     - Strategies can modify rewards dynamically based on distribution,
       performance, or context (including spatial context).
   * - **Equity optimization**
     - Reward structures can *balance* participation rather than amplify the
       gap between heavy and light users.

GAME is designed as a **programmable incentive engine**, not just a points
API.

Two integration modes
=====================

GAME is deliberately usable at two very different altitudes.

1. Full backend gamification platform
-------------------------------------

Use GAME as the complete gamification backend for your product:

* create and manage **games** (campaigns) and their **tasks**;
* assign **points** to users when they act;
* track **wallets** and convert points to **coins**;
* apply built-in or custom **strategies** per game/task;
* read aggregated analytics, KPIs, and per-event audit history.

2. Scoring microservice
-----------------------

Use GAME purely as an **incentive/scoring engine**. Your system owns the
application logic and the source of truth for users and tasks; it calls GAME
only to compute the scoring outcome:

#. The external system reports an event to GAME.
#. GAME runs the relevant strategy and returns ``points`` plus a
   ``caseName`` (the human-readable reason the rule matched).
#. The external system applies the result however it likes.

Because scoring is deterministic given the same inputs (see *Reproducibility*
below), the same event always yields the same score - which is what makes the
microservice mode safe to retry and to reason about.

Representative use cases
========================

GAME has been deployed and studied in **citizen science** and **spatial
crowdsourcing** contexts, where the goal is to keep volunteers engaged and to
*spread* effort across tasks and geographic areas rather than letting it
concentrate. Typical scenarios:

* Reward a user's **first contributions** generously to lower the activation
  barrier (basic engagement), then taper as they become regular.
* Pay a **bonus** when a user improves on their own previous performance, and
  a different bonus when they beat the global average - so both newcomers and
  top performers have a reason to act.
* Steer attention toward **cold spots** - tasks or regions with little
  activity - by making them temporarily worth more.

The :doc:`strategies` guide shows how each of these is expressed, either with
a built-in strategy or with the no-code DSL.

Properties that matter
======================

Two cross-cutting properties show up repeatedly and are worth internalizing
early.

Reproducibility & determinism
-----------------------------

GAME is built to support **scientific reproducibility** and deterministic
evaluation of strategies:

* **Deterministic execution** - identical inputs (tasks, parameters,
  timestamps, configuration) produce identical outputs.
* **Explicit parameterization** - scoring is driven by explicit strategy
  parameters stored in the database; there is no hidden global state.
* **Simulation mode** - strategies can be evaluated with ``isSimulated=true``
  (and a dedicated simulate endpoint) *without* touching ``UserPoints``, the
  wallet, or any other production data.
* **Versionable strategies** - custom strategies are versioned; publishing a
  new version never overwrites the running one until you say so.
* **Traceable execution** - sampled execution traces let you reconstruct *why*
  a rule matched weeks after the fact.

These properties let GAME double as a **reproducible experimental platform**
for studying adaptive incentive mechanisms - see the *Research & Publications*
section of the project ``README`` for the papers built on it.

Safety under failure
--------------------

GAME aims to behave predictably when things go wrong:

* **Idempotent** point assignment where an idempotency key is supplied, so a
  retried request does not double-award.
* Transactional database behavior, safe under concurrent requests.
* Deterministic auth failures - no silent fallback to an unauthenticated path.
* Bounded strategy execution - the DSL interpreter cannot run away with CPU
  or memory (see :doc:`dsl-engine`).

Where to go next
================

* :doc:`architecture` - the layered design and the life of a request.
* :doc:`domain-model` - the entities (games, tasks, users, points, wallets…)
  and how they relate.
* :doc:`getting-started` - install, configure, and make your first call.
