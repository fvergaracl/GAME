# `gd_set_points` - Set points (post-rules only)

Mutate the running `points` value. Unlike `gd_assign_points`, this
does NOT halt the program - subsequent statements in the same
`gd_post_rule` keep running.

## AST

```json
{
  "type": "set_points",
  "value": { "type": "arith", "op": "*",
             "left":  { "type": "field", "path": "parent.points" },
             "right": { "type": "literal", "value": 1.5 } }
}
```

## Example

> Multiply the parent's points by 1.5:

```
set_points = parent.points * 1.5
```

## Notes

* `value` must evaluate to a number - `DSL_SET_POINTS_NOT_NUMBER`
  otherwise.
* The mutation persists across subsequent post-rules in the same
  pipeline. To chain mutations across multiple rules, just stack them
  - each one reads what the previous one wrote via `parent.points`.

  Caveat: `parent.points` always carries the **original** parent
  result, not the running mutation. To read the current value use a
  literal expression that already reflects the chain.
