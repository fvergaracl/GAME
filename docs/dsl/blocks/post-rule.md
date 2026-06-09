# `gd_post_rule` - Post-rule (DSL_EXTEND)

A rule that runs **after** the parent built-in. Available statements
in the `then` slot are `gd_set_points`, `gd_set_case_name`,
`gd_set_callback_data`, and `gd_return`.

Post-rules can read the parent's result via `parent.points` /
`parent.case_name` (see [`gd_field_parent`](field-parent.md)).

## Example

> Multiply by 1.5 when the parent awarded `PerformanceBonus`:

```
when parent.case_name == "PerformanceBonus"
then set_points = parent.points * 1.5
     set_case_name = "BoostedPerformanceBonus"
```

## Notes

* Unlike main-section rules, `gd_set_points` does **not** halt - you
  can chain multiple `then` statements that all run.
* Post-rules see the (possibly mutated by pre-rules) `data` dict.
* If no post-rule matches, the parent's result is returned unchanged.
