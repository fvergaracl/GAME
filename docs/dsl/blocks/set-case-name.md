# `gd_set_case_name` - Set case name (post-rules only)

Override the case name the parent strategy emitted.

## AST

```json
{
  "type": "set_case_name",
  "value": { "type": "literal", "value": "BoostedPerformanceBonus" }
}
```

## Example

> Re-label the parent's `PerformanceBonus` after applying a multiplier:

```
when parent.case_name == "PerformanceBonus"
then set_points = parent.points * 1.5
     set_case_name = "BoostedPerformanceBonus"
```

## Notes

* `value` must evaluate to a string - `DSL_SET_CASE_NAME_NOT_STRING`
  otherwise.
* Like all post-rule statements, this does not halt.
* The new case name shows up in analytics. Renaming an existing case
  splits its time series, so prefer adding a NEW name (`BoostedX`) over
  reusing the parent's.
