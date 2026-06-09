# `gd_set_callback_data` - Set callback data

Add a key/value to the `callbackData` dict returned alongside points.
Useful when the caller wants context about *why* the points were
awarded (which threshold matched, the raw computed value, etc.).

## AST

```json
{
  "type": "set_callback_data",
  "key": "matchedThreshold",
  "value": { "type": "literal", "value": 0.5 }
}
```

## Example

> Echo back the raw score for the caller:

```
when data.score_raw > 0
then
  set_callback_data "raw_score" = data.score_raw
  assign 1 point caseName="Scored"
```

## Notes

* `set_callback_data` BEFORE `assign_points` accumulates. AFTER an
  `assign_points` they are unreachable (the program halted).
* Valid in all sections (`rules`, `default`, `pre_rules`, `post_rules`).
* Keys must match `[A-Za-z0-9_]+`. Nested structures are not
  supported.
