# `gd_func_call` - Function call

A whitelisted built-in function. No user-defined functions exist -
this is intentional, so the sandbox cannot grow new attack surfaces
through tenant code.

## Functions

| Name    | Arity | Behaviour                                            |
|---------|-------|------------------------------------------------------|
| `int`   | 1     | Truncate toward zero. `int(3.7)` → 3, `int(-1.5)` → -1. |
| `clamp` | 3     | `clamp(value, lo, hi)` → `max(lo, min(value, hi))`.  |

## AST

```json
{
  "type": "func_call",
  "name": "clamp",
  "args": [
    { "type": "field", "path": "data.score_raw" },
    { "type": "literal", "value": 0 },
    { "type": "literal", "value": 100 }
  ]
}
```

## Example

> Bound a raw score to `[0, 100]` before assigning:

```
assign  clamp(data.score_raw, 0, 100)  points
        caseName="Scaled"
```

## Notes

If you find yourself wanting a new function, file a ticket - adding
one is a backend change because the function must be vetted before
landing in the sandbox.
