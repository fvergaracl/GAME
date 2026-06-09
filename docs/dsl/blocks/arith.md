# `gd_arith` - Arithmetic

Binary arithmetic between two expressions.

## Operators

| Symbol | Meaning             |
|--------|---------------------|
| `+`    | addition            |
| `-`    | subtraction         |
| `*`    | multiplication      |
| `/`    | division (float)    |
| `min`  | minimum of two args |
| `max`  | maximum of two args |

## AST

```json
{
  "type": "arith",
  "op": "*",
  "left":  { "type": "field", "path": "user.measurements_count" },
  "right": { "type": "literal", "value": 2 }
}
```

## Example

> Double the measurement count:

```
user.measurements_count * 2
```

## Errors

* Division by zero raises `DSL_ARITH_DIV_BY_ZERO`. Guard with a
  preceding `compare ... != 0` rule.
* Mismatched types (e.g. string + number) raise
  `DSL_ARITH_TYPE_MISMATCH`.

## Notes

`min` and `max` only take two arguments here. For three-way clamping
use [`gd_func_call`](func-call.md) with `clamp(value, lo, hi)`.
