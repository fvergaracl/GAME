# `gd_and` — Logical AND

True when **both** arguments are true. Evaluates left-to-right with
short-circuit: if the first argument is false, the second is not
evaluated. Useful when the second argument is expensive (an analytics
field that triggers a DB query).

## AST

```json
{
  "type": "and",
  "args": [
    { "type": "compare", "..." },
    { "type": "compare", "..." }
  ]
}
```

## Example

> User has done at least 1 measurement AND their average time is under
> 30 seconds:

```
user.measurements_count >= 1  AND  user.avg_time < 30
```
