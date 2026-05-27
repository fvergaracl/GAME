# `gd_rule` — Rule

The root of a strategy program. A rule has two slots:

* **when** — a single condition (usually a `gd_compare`, `gd_and`,
  `gd_or`, or `gd_not`).
* **then** — a stack of statements that run if the condition is true.

The engine walks rules top-to-bottom. The **first** `assign_points`
statement reached inside a matching rule stops the whole program.
Statements that run before `assign_points` (e.g. `set_callback_data`)
accumulate into the response; statements after it never run.

## AST

```json
{
  "type": "rule",
  "id": "r1",
  "when": { "type": "compare", "..." },
  "then": [ { "type": "assign_points", "..." } ]
}
```

## Example

> If the user has fewer than 2 measurements, award 1 point with case
> name `BasicEngagement`.

```
when  user.measurements_count < 2
then  assign 1 point  caseName="BasicEngagement"
```

## Notes

* A rule with an empty `then` is allowed but does nothing — the
  validator warns rather than erroring.
* You typically want at least one `assign_points` inside every
  rule. If no rule matches the program returns `(0, null, {})`.
