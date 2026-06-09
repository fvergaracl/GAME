# `gd_field_parent` - Field (parent.\*)

(`post_rules` only) Read a value from the parent strategy's result. The
engine populates these paths after the parent runs and before
`post_rules` executes.

## Available paths

| Path                | Type                | Meaning                              |
|---------------------|---------------------|--------------------------------------|
| `parent.points`     | number              | Points the parent strategy emitted.  |
| `parent.case_name`  | string \| null      | Case name the parent emitted.        |

## AST

```json
{ "type": "field", "path": "parent.points" }
```

## Example

> Multiply by 1.5 when the parent emitted a `PerformanceBonus` case:

```
post_rule:
  when parent.case_name == "PerformanceBonus"
  then set_points = parent.points * 1.5
```

## Notes

* These paths are rejected by the validator anywhere outside
  `post_rules`. There is no equivalent in `pre_rules` because the
  parent hasn't run yet.
* If the parent returned `points=None` (no rule matched), `parent.points`
  reads as `0`.
