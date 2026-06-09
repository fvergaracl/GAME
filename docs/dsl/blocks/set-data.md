# `gd_set_data` - Set data (pre-rules only)

Write a key into the `data` dict the parent strategy will see. Valid
only inside `gd_pre_rule`.

## AST

```json
{
  "type": "set_data",
  "key": "duration_ms",
  "value": { "type": "arith", "op": "*",
             "left":  { "type": "field", "path": "data.duration_ms" },
             "right": { "type": "literal", "value": 2 } }
}
```

## Example

> Convert seconds to milliseconds before the parent strategy sees the
> measurement:

```
when data.duration_unit == "seconds"
then set_data "duration_ms" = data.duration_seconds * 1000
```

## Notes

* Keys must match `[A-Za-z0-9_]+`.
* Each `set_data` overwrites - there is no merge/append.
* `set_data` mutations are local to the request: the on-disk row is
  untouched, only the in-memory dict passed downstream changes.
