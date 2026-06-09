# `gd_literal_text` - Text literal

A constant string. Use as `case_name` of an `assign_points`, as the
value of a `set_callback_data`, or as the right-hand side of a string
comparison.

## AST

```json
{ "type": "literal", "value": "BasicEngagement" }
```

## Limits

* `case_name` values are constrained to printable ASCII, up to 200
  characters. The validator rejects strings with control characters.
* Arbitrary string compares (`data.kind == "video"`) are fine - the
  same character-set rule does NOT apply there.
