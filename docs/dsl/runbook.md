# DSL Strategy Runbook

What to do when a DSL strategy in production is misbehaving.

This runbook assumes you have read access to the GAME database
(`strategyexecutionlog`, `strategydefinition`) and to Prometheus /
Grafana for the metrics surfaced in [Sprint 11](../).

## Index

* [A published strategy is emitting wrong points](#wrong-points)
* [Latency alert fired (p99 > 250ms)](#latency)
* [Error rate alert fired](#errors)
* [Sandbox concerns — did a tenant exceed the limits?](#limits)
* [Strategy is taking down a realm](#kill-switch)

---

## <a id="wrong-points"></a> A published strategy is emitting wrong points

> "Tenant X says their users are getting +50% points everywhere, looks
> like a regression in their custom strategy."

### Step 1 — confirm which strategy is running

```sql
SELECT g.id, g."externalGameId", g."strategyId"
FROM games g
WHERE g."externalGameId" = '<gameId>';
```

If the `strategyId` starts with `custom:`, the rest of the UUID is a
`StrategyDefinition` row. Pull it:

```sql
SELECT id, name, version, status, "publishedAt", "createdBy"
FROM strategydefinition
WHERE id = '<uuid>';
```

### Step 2 — pull the most recent executions

```sql
SELECT created_at, status, "errorCode", points, "caseName",
       "externalUserId", "durationMs", "nodesExecuted"
FROM strategyexecutionlog
WHERE "strategyId" = '<uuid>'
ORDER BY created_at DESC
LIMIT 50;
```

Patterns to look for:

* All rows have `status = "ok"` but `points` is unexpectedly large →
  a `set_points` post-rule is multiplying.
* `caseName` is one you don't recognise → check post-rules for a
  `set_case_name` override.

### Step 3 — replay the failing input

For any row of interest, pull the `trace` JSONB column. Each entry
points back to a `nodeId` from the AST. Then call the simulate
endpoint with the same `externalGameId`, `externalTaskId`,
`externalUserId`, and `data` — simulate is side-effect-free.

```bash
curl -X POST .../v1/strategies/custom/<uuid>/simulate \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "externalGameId": "...",
    "externalTaskId": "...",
    "externalUserId": "...",
    "data": { ... }
  }'
```

The response carries the same trace shape — diff against the persisted
one to confirm reproducibility.

### Step 4 — rollback

```bash
# from the dashboard
Strategies → <name> → Version history → Rollback to vN-1
```

Or via API:

```bash
curl -X POST .../v1/strategies/custom/<uuid>/rollback/<version>
```

Rollback archives the broken version and re-publishes the older one.
The change applies on the next scoring event — no UserPoints are
rewritten retroactively.

### Step 5 — root-cause

After rollback, edit the broken version (it's `ARCHIVED` now; the
editor lets you copy it back into a `DRAFT`), reproduce the bug with
simulate, fix it, publish a new version.

---

## <a id="latency"></a> Latency alert fired

`DslExecutionLatencyHigh` fires when `histogram_quantile(0.99,
dsl_execution_duration_seconds)` exceeds 250 ms for 5 minutes.

### Confirm which realm and strategy is slow

```promql
topk(5,
  histogram_quantile(0.99,
    sum by (le, realm, strategy_type) (
      rate(dsl_execution_duration_seconds_bucket[5m])
    )
  )
)
```

### Pull the corresponding strategy

The metric is realm-keyed, not strategy-id-keyed. Cross-reference with
`strategyexecutionlog`:

```sql
SELECT "strategyId", percentile_cont(0.99)
  WITHIN GROUP (ORDER BY "durationMs") AS p99,
  count(*)
FROM strategyexecutionlog
WHERE "realmId" = '<realm>'
  AND created_at > now() - interval '15 minutes'
GROUP BY "strategyId"
ORDER BY p99 DESC
LIMIT 10;
```

### Likely causes

* **Heavy `field` usage**: each unique analytics path costs a query.
  Look at `nodesExecuted` and the unique field paths in the trace.
  Mitigation: drop unused field reads.
* **Postgres slow query**: check the slow query log for analytics
  queries (`get_avg_time_between_tasks_*`, etc.). The DSL itself is
  bounded by the timeout; if PG is slow, that's where the time goes.
* **Tenant-scale regression**: a realm grew 10× this week. Capacity
  problem, not a strategy bug.

### If the strategy itself is the problem

Roll it back (see [wrong points](#wrong-points)). The latency drops
within seconds because the engine resolves strategies per request.

---

## <a id="errors"></a> Error rate alert fired

`DslExecutionErrorRateHigh` fires when >1 % of executions in a realm
fail over 10 minutes.

### Find the error code

```promql
topk(5,
  sum by (realm, code) (
    rate(dsl_execution_errors_total[10m])
  )
)
```

Error codes are listed in `app/core/exceptions.py` (search for
`code="DSL_"`). Common ones:

| Code                          | What it means                                   |
|-------------------------------|-------------------------------------------------|
| `DSL_TIMEOUT`                 | Strategy didn't finish within 500 ms.           |
| `DSL_LIMIT_EXCEEDED`          | Hit the node-count or depth cap.                |
| `DSL_ARITH_DIV_BY_ZERO`       | A `/` operator ran with a zero denominator.     |
| `DSL_COMPARE_TYPE_MISMATCH`   | Compared a number to a string (or null).        |
| `DSL_FIELD_NOT_PRECOMPUTED`   | Field path bypassed the validator (bug — page!).|

### Pull the failing rows

```sql
SELECT created_at, "errorCode", trace, notes
FROM strategyexecutionlog
WHERE "realmId" = '<realm>'
  AND status != 'ok'
  AND created_at > now() - interval '15 minutes'
ORDER BY created_at DESC
LIMIT 20;
```

Error rows are **always** persisted (no sampling), so you should see
every failure in the window.

### Fixing common errors

* `DSL_ARITH_DIV_BY_ZERO`: wrap the divisor in a `compare ... != 0`
  guard rule.
* `DSL_COMPARE_TYPE_MISMATCH`: typically a `data.<key>` missing. Add a
  `data.<key> != null` guard.
* `DSL_TIMEOUT`: see [latency](#latency). The most common cause is
  many analytics fields in a single program.

---

## <a id="limits"></a> Sandbox concerns

If you suspect a tenant is trying to break out of the sandbox:

* `DSL_FIELD_NOT_PRECOMPUTED` is the canary. A handful of these may
  be a stale validator; sustained bursts mean someone is hand-crafting
  payloads that bypass the dashboard validator and POSTing them raw.
* `DSL_UNKNOWN_STATEMENT` / `DSL_UNKNOWN_EXPRESSION` similar.

The interpreter table-dispatches on node type — there is no
`getattr`/`eval` path — so even a successful bypass cannot execute
arbitrary Python. But the field whitelist is the perimeter for what a
strategy can READ; do not relax it without a security review.

If you see these codes, capture the offending request from access
logs and forward to the security team.

---

## <a id="kill-switch"></a> Kill switch

If a tenant's strategy is taking down their realm AND the rollback
endpoint is unreachable for some reason, the brute-force option is to
manually flip the row:

```sql
UPDATE strategydefinition
SET status = 'ARCHIVED'
WHERE id = '<uuid>'
  AND status = 'PUBLISHED';
```

Then the engine falls back to whatever the previous published version
was (none → the engine raises `NotFoundError` for that tenant; better
than a runaway custom rule).

This is a last resort. Prefer `/rollback`.

---

## Useful queries

```sql
-- Per-strategy execution volume + p99 over the last hour
SELECT "strategyId",
       count(*) as runs,
       avg("durationMs") as avg_ms,
       percentile_cont(0.99) WITHIN GROUP (ORDER BY "durationMs") as p99_ms,
       sum(case when status != 'ok' then 1 else 0 end) as failures
FROM strategyexecutionlog
WHERE created_at > now() - interval '1 hour'
GROUP BY "strategyId"
ORDER BY runs DESC;
```

```sql
-- All errors in the last hour with their codes
SELECT "errorCode", count(*)
FROM strategyexecutionlog
WHERE status != 'ok' AND created_at > now() - interval '1 hour'
GROUP BY "errorCode"
ORDER BY count(*) DESC;
```
