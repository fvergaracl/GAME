# `gd_compare` - Compare

Compare two values and return a boolean. Operands can be any
expression: literals, fields, arithmetic, function calls.

## Operators

| Symbol | Meaning              |
|--------|----------------------|
| `<`    | strictly less than   |
| `<=`   | less or equal        |
| `==`   | equal                |
| `!=`   | not equal            |
| `>=`   | greater or equal     |
| `>`    | strictly greater     |

## AST

```json
{
  "type": "compare",
  "op": "<",
  "left":  { "type": "field", "path": "user.measurements_count" },
  "right": { "type": "literal", "value": 2 }
}
```

## Example

> User has done fewer than 2 measurements:

```
user.measurements_count < 2
```

## Notes

* Comparing incompatible types (e.g. a number against a string) raises
  `DSL_COMPARE_TYPE_MISMATCH` at runtime. The validator catches the
  common cases statically; obscure ones surface in simulation.
* `==` is structural equality. Floats are compared with `==`, so beware
  of precision when comparing the result of arithmetic against a
  literal. Prefer `<` / `<=` over `==` for thresholds.
