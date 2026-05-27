# `gd_or` — Logical OR

True when **at least one** argument is true. Short-circuits on the
first `true`. The arguments must each be a condition (compare, and,
or, not, or a literal `true`/`false`).

## AST

```json
{
  "type": "or",
  "args": [
    { "type": "compare", "..." },
    { "type": "compare", "..." }
  ]
}
```

## Example

> Trigger when the user is on their first measurement OR has fewer than
> 100 measurements total:

```
user.measurements_count == 0  OR  user.measurements_count < 100
```
