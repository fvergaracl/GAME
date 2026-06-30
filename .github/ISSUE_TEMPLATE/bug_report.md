---
name: Bug report
about: Report a defect in the GAME backend (API, scoring engine, or DSL)
title: "[bug] "
labels: bug
assignees: ''

---

**Describe the bug**
A clear and concise description of what is wrong.

**Environment**
- GAME version / commit: <!-- e.g. v1.3.000, or the git SHA you are running -->
- Deployment mode: <!-- make dev / docker-compose / Kubernetes / bare Poetry -->
- Python version (only if running bare): <!-- e.g. 3.12.x -->

**Affected endpoint**
- Method + path: <!-- e.g. POST /api/v1/games/{gameId}/tasks/{externalTaskId}/points -->
- Auth used: <!-- X-API-Key or OAuth2 bearer -->

**Strategy involved** (if the bug is scoring-related)
- Type: <!-- built-in class / DSL (custom:<uuid>) / not applicable -->
- strategyId: <!-- e.g. default, socio_bee, custom:... -->

**To reproduce**
Minimal steps or a `curl` that triggers it:
1.
2.

**Expected behavior**
What you expected to happen.

**Actual behavior / response**
The actual HTTP status and response body, if any.

**Logs**
Relevant server output, e.g. `docker logs GAME_API_DEV`. A "Network Error" in
the dashboard is usually a backend 500 masked by CORS, so please include the
API logs.

```text
<paste logs here>
```

**Additional context**
Anything else that helps us reproduce or understand the problem.
