================================================
ADR 0007: The DSL is a sandboxed AST interpreter
================================================

:Status: Accepted

Context
=======

Custom scoring strategies are authored in a browser by people who are not GAME
developers, then run on the scoring hot path. Executing arbitrary user code
there is a non-starter, both for safety (no arbitrary Python) and for
stability (no unbounded CPU).

Decision
========

A custom strategy is a JSON AST walked node-by-node through a fixed handler
table (``app/engine/dsl_interpreter.py``). The design rests on four
guarantees:

#. **No dynamic Python** - no ``eval``, ``exec`` or ``getattr`` on AST-supplied
   strings; an unknown node type is rejected.
#. **Whitelist** - node types, operators, functions and field paths must each
   appear in an allow-list in ``app/engine/dsl_ast.py``, checked up front.
#. **Frozen precomputed context** - field access is a lookup in a frozen dict
   that ``ExecutionContext.build_for_ast`` precomputes; the walk never touches
   the database.
#. **Cooperative-yield cancellation** - the walk awaits ``asyncio.sleep(0)``
   periodically so a CPU-bound tree can actually be cancelled by the timeout.

Consequences
============

* Execution is bounded, deterministic, cancellable, and injection-proof.
* The DSL is intentionally a small *total* language, not general-purpose; node
  and depth limits cap expressiveness.

See also
========

* :doc:`/dsl-engine` - the interpreter, validator and limits in depth.
* :doc:`/security` - why untrusted scoring logic is sandboxed.
