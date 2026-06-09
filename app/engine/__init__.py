"""Strategy engine — adaptive and deterministic scoring.

This package computes how many points an event is worth. It contains the
built-in strategies (subclasses of
:class:`app.engine.base_strategy.BaseStrategy`, registered under stable public
ids via ``@register_strategy``) and the sandboxed **DSL** pipeline — validator,
execution context, and interpreter — that runs user-authored custom
strategies. See :doc:`the engine internals </dsl-engine>` for the full design.
"""
