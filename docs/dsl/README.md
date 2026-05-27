# DSL Strategy Editor — User Documentation

This is the entry point for game designers using the Strategy Editor in
the GAME dashboard. The editor lets you define how points are awarded
when a user completes a task, without writing Python.

A strategy is a tree of **blocks** assembled in the editor. When a
scoring event arrives the engine walks your tree top-to-bottom and
emits the first `assign_points` it reaches inside a matching rule.

## Modes

Two creation modes are available from the editor:

* **DSL_FULL** — you write the whole strategy from scratch.
* **DSL_EXTEND** — you start from a built-in (e.g. `default`) and
  layer `pre_rules` (which may mutate the input or veto the
  assignment) and `post_rules` (which may multiply points, override
  case names, or add callback data).

## Sections of a program

| Section          | What it does                                              | Modes      |
|------------------|-----------------------------------------------------------|------------|
| `rules`          | Main top-down list of conditional rules. First match emits points. | DSL_FULL   |
| `default`        | Fallback statement when no rule matches.                  | DSL_FULL   |
| `pre_rules`      | Rules that run *before* the parent strategy.              | DSL_EXTEND |
| `post_rules`     | Rules that run *after* the parent strategy.               | DSL_EXTEND |
| `parent_variables` | Per-realm overrides applied to the parent built-in.     | DSL_EXTEND |

## Blocks

See the per-block reference under [`blocks/`](blocks/). Every block
links to the same documentation page from the Blockly right-click
menu so you can jump from the editor straight to the explanation.

| Block                       | What it does                                                 |
|-----------------------------|--------------------------------------------------------------|
| [`gd_rule`](blocks/rule.md) | A `when … then …` rule. The root statement of a strategy.    |
| [`gd_compare`](blocks/compare.md) | Compare two values: `<`, `<=`, `==`, `!=`, `>=`, `>`.    |
| [`gd_and`](blocks/and.md)   | Logical AND of two conditions.                               |
| [`gd_or`](blocks/or.md)     | Logical OR of two conditions.                                |
| [`gd_not`](blocks/not.md)   | Logical negation.                                            |
| [`gd_field`](blocks/field.md) | Read a precomputed analytics value (count, avg time…).     |
| [`gd_field_data`](blocks/field-data.md) | Read a key from the per-event `data` payload.    |
| [`gd_field_parent`](blocks/field-parent.md) | (`post_rules` only) Read the parent strategy's points or case name. |
| [`gd_literal_number`](blocks/literal-number.md) | A constant number.                          |
| [`gd_literal_text`](blocks/literal-text.md) | A constant string.                              |
| [`gd_arith`](blocks/arith.md) | Binary arithmetic: `+`, `-`, `*`, `/`, `min`, `max`.       |
| [`gd_func_call`](blocks/func-call.md) | Built-in functions: `int(x)`, `clamp(x, lo, hi)`.  |
| [`gd_assign_points`](blocks/assign-points.md) | Award N points with a case name and stop.   |
| [`gd_set_callback_data`](blocks/set-callback-data.md) | Add a key to the response payload. |
| [`gd_pre_rule`](blocks/pre-rule.md) | Rule that runs before the parent strategy.           |
| [`gd_post_rule`](blocks/post-rule.md) | Rule that runs after the parent strategy.          |
| [`gd_set_data`](blocks/set-data.md) | (`pre_rules` only) Mutate the data dict before the parent sees it. |
| [`gd_veto`](blocks/veto.md) | (`pre_rules` only) Stop the pipeline before the parent runs. |
| [`gd_set_points`](blocks/set-points.md) | (`post_rules` only) Mutate the points from the parent. |
| [`gd_set_case_name`](blocks/set-case-name.md) | (`post_rules` only) Override the case name from the parent. |
| [`gd_parent_variable_override`](blocks/parent-variable-override.md) | Override a per-realm variable on the parent. |

## Limits

The engine enforces hard ceilings on every published strategy to keep a
runaway rule from impacting your tenant or others:

| Limit                  | Default | Configurable via env |
|------------------------|---------|----------------------|
| Wall-clock per call    | 500 ms  | `DSL_EXECUTION_TIMEOUT_MS` |
| AST nodes visited      | 1000    | `DSL_MAX_NODES`       |
| Recursion depth        | 32      | `DSL_MAX_DEPTH`       |

If your strategy hits a limit the event is rejected with a clear error
code. See the [runbook](runbook.md) for what to do next.

## Testing a strategy before publishing

Every strategy has a **Test** button in the editor. It calls
`POST /v1/strategies/custom/{id}/simulate` and shows you the full
node-by-node trace — exactly what would happen at runtime. Use this
liberally: simulation never touches `UserPoints`, the wallet, or any
other production data.

## Versioning

Every save of a `PUBLISHED` strategy creates a `v+1` `DRAFT` rather
than overwriting. The published version stays in production until you
explicitly publish v+1 or rollback to an older version. This means:

* You can experiment safely; nothing in production changes until you
  press Publish.
* If a published version misbehaves you can rollback to the previous
  one (see the runbook).

## Observability

Every execution of a custom strategy in production:

1. Emits Prometheus metrics: `dsl_execution_duration_seconds`,
   `dsl_execution_nodes_total`, `dsl_execution_errors_total`.
2. Persists a row in `strategyexecutionlog` if it failed, or with
   probability `DSL_EXECUTION_LOG_SAMPLE_RATE` (default 5%) if it
   succeeded.

This lets the on-call team and the strategy author both look back at
what a strategy did weeks after the fact without having to re-run
production traffic.
