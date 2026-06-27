# Data Retention & Privacy

GAME is used in citizen-science deployments, so the data it persists about
identifiable participants falls under GDPR. This document records **what
personal data is stored, the retention/anonymization policy, and how to honour
erasure requests**.

> Status: this is the **policy of record**. The automated retention cleanup is
> a tracked follow-up — today the deletes below are run manually/operationally,
> not by a scheduled job.

## What personal data is stored

### `logs` table (live audit log)
Written by `app.util.add_log.add_log` (via the `AuditLogger` in
`app/middlewares/auth_context.py`). Each row may contain:

| Column | Personal data? | Notes |
| --- | --- | --- |
| `oauth_user_id` | **Yes** | OAuth subject — directly identifies the human. |
| `apiKey_used` | Indirect | Public **prefix** only (e.g. `gme_live_3f6a9e0f`), never the secret. |
| `message` | Possibly | Free text — keep it generic. |
| `details` (JSON) | **Highest risk** | Arbitrary caller-supplied context. |
| `created_at` / `updated_at` | Indirect | Activity timestamps tied to the user. |

### `api_requests` table (dormant)
The `ApiRequests` model + repository + service exist, but **no code writes to
it** today — there is no request-logging middleware. It is an unused per-user
access-log schema (`userId`, `endpoint`, method, status, latency). It stores no
data in practice. **If it is ever wired up, it must adopt this same retention
policy from day one** (it would otherwise become an unbounded per-user access
log).

### Sentry (error monitoring)
Configured in `app/main.py` from `app/core/config.py`. Privacy-conservative by
default (see [Sentry posture](#sentry-posture)).

## Retention policy

- **`logs`:** retain **180 days**, then hard-delete. 180 days preserves
  audit/security value while honouring data minimization.

  ```sql
  DELETE FROM logs WHERE created_at < now() - interval '180 days';
  ```

- **`api_requests`:** no data today. If activated, apply the same 180-day
  window.

## Data minimization rule for `logs.details`

`details` is the main exposure because it accepts an arbitrary dict. Contributors
adding audit calls **must not** put the following in `message`/`details`:

- raw request/response bodies,
- secrets or full API keys (the prefix is fine),
- client IP addresses unless strictly required for a specific security event,
- any personal data beyond the `oauth_user_id` already on the row.

Prefer stable identifiers and error codes over free-form payloads.

## Subject rights (erasure)

To satisfy a right-to-be-forgotten request for a given OAuth subject, delete
their audit rows:

```sql
DELETE FROM logs WHERE oauth_user_id = :oauth_user_id;
```

(Other user-linked data — points, wallet, etc. — is out of scope for this
document and handled by the relevant domain services.)

## Sentry posture

Defaults are conservative so a production deployment that only sets `SENTRY_DSN`
does not leak PII or over-collect:

| Setting | Default | Effect |
| --- | --- | --- |
| `SENTRY_SEND_DEFAULT_PII` | `false` | No user ids / IP / headers / bodies attached to events. |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Samples 10% of traces (not every request). |
| `SENTRY_PROFILING_ENABLED` | `false` | Continuous profiler off. |

Operators can opt into richer collection per environment by setting those env
vars (e.g. a short local debugging session with `SENTRY_TRACES_SAMPLE_RATE=1.0`).
