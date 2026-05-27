# `gd_veto` — Veto (pre-rules only)

Cancel the rest of the pipeline. After a veto fires:

* The parent strategy does NOT run.
* The `post_rules` phase is skipped entirely.
* The program returns `points=0`, `case_name=<the veto's case_name>`,
  plus any `callback_data` accumulated before the veto.

## AST

```json
{
  "type": "veto",
  "case_name": "AbuseDetected"
}
```

## Example

> Reject scoring events whose `duration_ms` is negative:

```
when data.duration_ms < 0
then veto caseName="InvalidPayload"
```

## Notes

* Use sparingly. A veto is a hard "no points"; if you just want to
  scale down, mutate `data` with `set_data` and let the parent decide.
* The `case_name` shows up in analytics dashboards alongside normal
  case names. Prefix it (e.g. `VETO_*`) to make filtering easy.
