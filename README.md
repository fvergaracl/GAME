<div align="center">

# GAME - Goals And Motivation Engine

**An adaptive gamification engine for programmable, behavior-aware incentives.**

[![Tests](https://github.com/fvergaracl/GAME/actions/workflows/pytest.yml/badge.svg)](https://github.com/fvergaracl/GAME/actions/workflows/pytest.yml)
[![Lint](https://github.com/fvergaracl/GAME/actions/workflows/lint.yml/badge.svg)](https://github.com/fvergaracl/GAME/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/fvergaracl/GAME/branch/main/graph/badge.svg?token=R0MGAOMUBU)](https://codecov.io/gh/fvergaracl/GAME)
[![Docs](https://github.com/fvergaracl/GAME/actions/workflows/deploy_documentation.yml/badge.svg)](https://github.com/fvergaracl/GAME/actions/workflows/deploy_documentation.yml)

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)
[![GitHub stars](https://img.shields.io/github/stars/fvergaracl/GAME)](https://github.com/fvergaracl/GAME/stargazers)

<img src="GAME_logo.png" alt="GAME Logo" width="320">

</div>

GAME turns user activity into points, coins, and behavioral incentives through
**programmable scoring strategies**. Unlike static points APIs whose rules are
frozen at design time, a GAME strategy can react to behavior, context, and
system state, so incentives can be redistributed toward under-engaged users,
tasks, or regions instead of amplifying participation inequality.

> **New here?** Bring the whole stack up with one command - `make dev`
> (Linux/macOS/WSL) or `.\start.ps1` (Windows). Want to contribute? Jump to
> [Contributing](#contributing) - newcomers are very welcome.

---

## Why GAME?

- **Adaptive, not static** - scoring rules react to behavior, context, or
  system state instead of being frozen constants.
- **Redistributes participation** - incentives can shift effort toward
  under-engaged users, tasks, or regions rather than rewarding only the
  already-active.
- **Two altitudes** - run it as a complete gamification backend, or as a pure
  scoring microservice your system calls to compute *how many* points an event
  is worth.

## Architecture

A layered request flow, wired by a dependency-injection container:

```
Request -> Endpoint -> Service -> Strategy Engine -> Repository -> Database
```

Endpoints handle HTTP, auth, and validation; services hold business logic and
transactions; the **strategy engine** (`app/engine/`) computes scores;
repositories abstract persistence over PostgreSQL.

## Strategy model

A strategy is the scoring brain bound to a game (or an individual task). GAME
gives you **two ways to author one**:

- **Built-in classes (Python)** - subclasses of `BaseStrategy` registered in
  the engine; the stable path for engineers, with `default` as the safe
  baseline.
- **No-code DSL** - strategies authored visually in the dashboard, stored as
  `custom:<uuid>` and run inside a sandbox; the path for designers, with no
  Python.

See [strategies](docs/source/strategies.rst) for which model to pick, the
Python scoring contract, and the built-in catalogue. Per-subsystem maturity is
tracked in [ROADMAP.md](ROADMAP.md).

## Quick start

The fastest path brings up the **entire stack** - API, PostgreSQL, Keycloak,
dashboard, Prometheus, and Grafana. The first run creates `.env` from
`.env.sample`, builds the images, and waits until the API is healthy (no prior
`poetry install` needed).

```bash
make dev      # build + start the dev stack (Linux/macOS/WSL)
make logs     # tail logs (make logs-api for just the API)
make down     # stop and remove containers
make clean    # stop and delete all data volumes (destructive)
```

Windows uses `start.ps1` from PowerShell (no Docker Desktop required):

```powershell
.\start.ps1            # start  (-Logs to follow, -Down to stop, -Clean to wipe data)
```

Once the stack is up:

| Service | URL |
| --- | --- |
| API (Swagger) | http://localhost:8000/docs |
| Dashboard | http://localhost:3000 |
| Keycloak | http://localhost:8080 |
| Grafana | http://localhost:3001 (`admin`/`admin`) |
| Prometheus | http://localhost:9090 |

<details>
<summary>Prefer to run the API directly with Poetry?</summary>

```bash
git clone https://github.com/fvergaracl/GAME.git && cd GAME
poetry install
cp .env.sample .env                       # then edit secrets
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload  # Swagger at /docs, ReDoc at /redocs
```

Use the `KEYCLOAK_*` values from `.env.sample` (realm `GameRealm`, client
`game-backend`). The [getting-started](docs/source/getting-started.rst) guide
walks through obtaining a token and an API key end to end.

</details>

## API example (end-to-end)

Create a game, add a task, assign points, read the score (API-key auth):

```bash
# Create a game
GAME_ID=$(curl -s -X POST "http://localhost:8000/api/v1/games" \
  -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"externalGameId":"game-001","platform":"web","strategyId":"default"}' \
  | jq -r '.gameId')

# Add a task
curl -s -X POST "http://localhost:8000/api/v1/games/$GAME_ID/tasks" \
  -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"externalTaskId":"task-login"}'

# Assign points -> {"points":1,"caseName":"BasicEngagement", ...}
curl -s -X POST "http://localhost:8000/api/v1/games/$GAME_ID/tasks/task-login/points" \
  -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
  -d '{"externalUserId":"user-123"}'

# Read the user's points
curl -s "http://localhost:8000/api/v1/users/user-123/points" -H "X-API-Key: $API_KEY"
```

Obtaining a token and creating `$API_KEY` is covered in
[getting-started](docs/source/getting-started.rst) and
[authentication](docs/source/authentication.rst).

## Documentation

The full documentation is published as a **Sphinx site** (organized along the
[Diátaxis](https://diataxis.fr/) model) and built from
[`docs/source/`](docs/source/); every running instance also serves an
interactive API reference at `/docs` (Swagger) and `/redocs` (ReDoc).

Start at the [documentation index](docs/source/index.rst), then jump by goal:

- **Call the API** -> [getting-started](docs/source/getting-started.rst)
- **Integrate GAME** -> [integrating](docs/source/integrating.rst),
  [strategies](docs/source/strategies.rst)
- **Understand how it works** -> [overview](docs/source/overview.rst),
  [architecture](docs/source/architecture.rst)
- **Run it in production** -> [configuration](docs/source/configuration.rst),
  [operations](docs/source/operations.rst),
  [security](docs/source/security.rst)

Build it locally with `poetry run sphinx-build -b html docs/source _build/html`.

## Testing

```bash
poetry run pytest      # full suite + coverage gate
```

See [TESTING.md](TESTING.md) and
[contributing](docs/source/contributing.rst) for the unit, E2E, and load
runners (`scripts/run_*`) and the coverage gate.

## Roadmap

What is stable, experimental, and planned (refunds, spatial scoring, transfers)
is tracked honestly in [ROADMAP.md](ROADMAP.md).

## Contributing

GAME is open source, and contributions of **all experience levels** are welcome
- bug fixes, new scoring strategies, docs, or tests.

1. **Fork** the repo and create a feature branch.
2. **Install** with `poetry install` and set up the pre-commit hooks.
3. **Make your change with tests**, then run `poetry run pytest` and the
   linters.
4. **Open a pull request** using the template; CI runs lint, tests, and the
   coverage gate.

Browse [good first issues](https://github.com/fvergaracl/GAME/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22),
read **[CONTRIBUTING.md](CONTRIBUTING.md)**, and uphold our
**[Code of Conduct](CODE_OF_CONDUCT.md)**. Found a security issue? Follow the
**[Security Policy](SECURITY.md)** instead of opening a public issue.

## Citing GAME

If you use GAME in your research, please cite it via
**[CITATION.cff](CITATION.cff)** - GitHub's "Cite this repository" button reads
it. That file also lists the peer-reviewed papers built on GAME (SOCIO-BEE,
spatial crowdsourcing, GREENCROWD).

## License

GAME is released under the **[Apache License 2.0](LICENSE)** - free to use,
modify, and distribute, including commercially, provided you retain the license
and attribution.

## Contact

- **Bugs & features** -> [GitHub Issues](https://github.com/fvergaracl/GAME/issues)
- **Questions & ideas** -> [GitHub Discussions](https://github.com/fvergaracl/GAME/discussions)
- **Security** -> [SECURITY.md](SECURITY.md)
- **Maintainer** -> Felipe Vergara-Borge ([felipe.vergara@deusto.es](mailto:felipe.vergara@deusto.es))

If GAME is useful to you, please consider starring the repo and citing it.
