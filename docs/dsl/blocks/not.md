# `gd_not` — Logical NOT

Negates one condition.

## AST

```json
{
  "type": "not",
  "arg": { "type": "compare", "..." }
}
```

## Example

> User is NOT on their first measurement:

```
not (user.measurements_count == 0)
```

## Notes

`not (a < b)` is the same as `a >= b`. The validator does not rewrite
this for you; pick whichever reads better.
