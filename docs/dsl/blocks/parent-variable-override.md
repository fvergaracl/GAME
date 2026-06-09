# `gd_parent_variable_override` - Override parent variable

Adjust a per-realm variable on the parent built-in **without** writing
custom logic. Variables come from the parent strategy's
`get_variables()` method; the editor surfaces a dropdown listing them.

## AST

These live under `program.parent_variables` (not inside a rule):

```json
{
  "type": "program",
  "parent_variables": {
    "variable_basic_points": 5,
    "variable_bonus_points": 20
  },
  "pre_rules": [...],
  "post_rules": [...]
}
```

## Example

> Use the parent's `default` strategy but with `variable_basic_points`
> bumped to 5 instead of the registry's default of 1.

```
parent_variables:
  variable_basic_points = 5
```

## Notes

* The override is **per-realm**, not global - your custom strategy
  carries its own copy of the parent variables; other realms still see
  the original defaults.
* Only keys present in `parent.get_variables()` are accepted; unknown
  keys fail validation at create-time.
* Values must be JSON scalars (number, string, bool). Nested
  structures are rejected.
