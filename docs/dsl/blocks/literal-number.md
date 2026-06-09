# `gd_literal_number` - Number literal

A constant numeric value. Use anywhere an expression is expected:
inside compares, arithmetic, `assign_points` values, etc.

## AST

```json
{ "type": "literal", "value": 1.5 }
```

## Notes

* Integers and floats are interchangeable - the interpreter treats
  them as Python numbers.
* No range limit, but the validator rejects literal `inf` / `NaN`.
