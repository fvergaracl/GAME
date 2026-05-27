# `gd_pre_rule` — Pre-rule (DSL_EXTEND)

A rule that runs **before** the parent built-in. Available statements
in the `then` slot are `gd_set_data`, `gd_veto`,
`gd_set_callback_data`, and `gd_return`.

## AST

Pre-rules live in the program's `pre_rules` list (not in `rules`):

```json
{
  "type": "program",
  "pre_rules": [
    { "type": "rule", "when": { ... }, "then": [ ... ] }
  ],
  "post_rules": [],
  "parent_variables": { ... }
}
```

## Example

> Halve the user's reported `duration_ms` if it's suspiciously low,
> before the parent calculates points:

```
when data.duration_ms < 100
then set_data "duration_ms" = data.duration_ms * 2
```

## Notes

* Pre-rules can mutate the `data` dict via `gd_set_data`. The mutated
  dict is what the parent strategy sees.
* If a pre-rule fires `gd_veto`, the parent never runs and the entire
  `post_rules` phase is skipped. The veto's `case_name` is the final
  result.
