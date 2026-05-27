# `gd_field` — Field

Read a value precomputed by the engine before your strategy runs. The
dropdown only lists paths the engine knows how to compute — there is
no way to read arbitrary attributes.

## Available paths

| Path                              | Meaning                                                        |
|-----------------------------------|----------------------------------------------------------------|
| `externalGameId`                  | The game id from the scoring event.                            |
| `externalTaskId`                  | The task id from the scoring event.                            |
| `externalUserId`                  | The user id from the scoring event.                            |
| `user.measurements_count`         | How many measurements this user has on this task (lifetime).   |
| `user.recent_measurements_count`  | Same, restricted to the last 300 seconds.                      |
| `task.measurements_count`         | How many measurements **any** user has on this task.           |
| `user.avg_time`                   | This user's average time between measurements (on this task).  |
| `all.avg_time`                    | Average time between measurements across all users (this task).|
| `user.last_window_diff`           | Time-window diff between the last two measurements (this user).|
| `user.new_last_window_diff`       | Same, including the in-flight measurement.                     |

## AST

```json
{ "type": "field", "path": "user.measurements_count" }
```

## Notes

* Field values are precomputed in a single batch before your AST runs.
  This means using the same field 10 times costs the same as using it
  once — no N+1.
* `data.<key>` reads come from `gd_field_data` instead.
* Paths starting with `parent.` (e.g. `parent.points`,
  `parent.case_name`) are only valid in `post_rules` — see
  [`gd_field_parent`](field-parent.md).
