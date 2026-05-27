# `gd_assign_points` — Assign points

The terminal statement of a `gd_rule`. Sets the points emitted by the
program and stops execution — no further rules run, no statements
after this one run.

## AST

```json
{
  "type": "assign_points",
  "value": { "type": "literal", "value": 1 },
  "case_name": "BasicEngagement"
}
```

## Example

> Award 10 points with case `PerformanceBonus`:

```
assign 10 points  caseName="PerformanceBonus"
```

## Notes

* `value` must evaluate to a number — `DSL_ASSIGN_POINTS_NOT_NUMBER`
  otherwise.
* `case_name` is mandatory. Pick a stable label per scenario; analytics
  buckets events by `case_name`, so renaming it splits the time series.
* This statement is illegal inside `pre_rules` and `post_rules` — use
  `gd_veto` (pre) or `gd_set_points` (post) instead. The validator
  rejects misplaced ones at create-time.
