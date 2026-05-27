# `gd_field_data` — Field (data.\*)

Read a key from the per-event `data` payload passed by the caller.
This is how you reach values your scoring caller chooses to attach
(e.g. `data.duration_ms`, `data.score_raw`).

## AST

```json
{ "type": "field", "path": "data.score_raw" }
```

The key after `data.` must match `[A-Za-z0-9_]+`. Nested keys are not
supported — flatten them on the caller side.

## Example

> Bonus when `data.streak` is at least 3:

```
data.streak >= 3
```

## Notes

* Missing keys read as `null`. Comparing `null` with a number raises
  `DSL_COMPARE_TYPE_MISMATCH`; defend with `data.streak != null` if
  the key is optional.
* The validator does not enforce that a key exists in `data` because
  it can vary per request — runtime gives the precise error.
