<div align="center">

# GAME — Goals And Motivation Engine

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

GAME is an **adaptive gamification engine** designed to dynamically shape participation, incentives, and behavioral outcomes through programmable scoring strategies. It exposes APIs to manage games, tasks, point assignment, wallets, and strategy-driven scoring behavior.

> **New here?** Get the whole stack running with a single command — `make dev`
> (Linux/macOS/WSL) or `.\start.ps1` (Windows); see
> [Running with Docker](#running-with-docker). Want to contribute? Jump to
> [Contributing & Community](#contributing--community) — newcomers are very welcome.

---

## Table of Contents

- [Why GAME?](#why-game)
- [Architecture Overview](#architecture-overview)
- [Strategy Model](#strategy-model)
- [Integration Patterns](#integration-patterns)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Keycloak OAuth (Dev)](#keycloak-oauth-dev)
- [API Example (End-to-End)](#api-example-end-to-end)
- [Running with Docker](#running-with-docker)
- [Tests & Coverage](#tests--coverage)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Production & Reliability](#production--reliability)
- [Reproducibility & Determinism](#reproducibility--determinism)
- [Strategy Evaluation & Metrics](#strategy-evaluation--metrics)
- [Contributing & Community](#contributing--community)
- [How to Cite GAME](#how-to-cite-game)
- [Research & Publications](#research--publications)
- [License](#license)
- [Contact & Support](#contact--support)

---

## Why GAME?

Most gamification systems are **static**: rules and rewards are fixed, producing predictable engagement patterns and often reinforcing participation inequality.

GAME introduces **adaptive gamification**, enabling:

- **Adaptive vs static gamification**: scoring rules can react to behavior, context, or system state.
- **Behavioral redistribution**: incentives can shift participation toward under-engaged users, tasks, or areas.
- **Spatial / incentive shaping**: strategies can modify rewards dynamically based on distribution, performance, or context.
- **Equity / participation optimization**: reward structures can balance participation instead of amplifying inequality.

GAME is designed as a **programmable incentive engine**, not just a points API.

---

## Architecture Overview

```
Request → Endpoint → Service → Strategy Engine → Repository → Database
```

**Responsibilities**

- **Endpoints**: HTTP interface, validation, authentication, orchestration.
- **Services**: business logic, transactional behavior, domain rules.
- **Strategy Engine (`app/engine/`)**: adaptive scoring logic and behavioral rules.
- **Repositories**: persistence abstraction (SQLModel / SQLAlchemy).
- **Database**: PostgreSQL storage layer.

This layered design allows **pluggable strategies, deterministic services, and reproducible behavior**.

---

## Strategy Model

Strategies define how points and incentives are computed.

### Types

- **Deterministic strategies**: fixed rule-based scoring.
- **Adaptive strategies**: dynamic scoring based on context, distribution, or system state.

### Characteristics

- Strategies live in `app/engine/`.
- Strategies are **pluggable** and selected via `strategyId`.
- A **game defines a base strategy**, tasks may override it.
- Strategies can use inputs such as:
  - task parameters
  - historical behavior
  - distribution state
  - contextual metadata

### Adding a new strategy (minimal steps)

1. Create a new class in `app/engine/` inheriting from `BaseStrategy`.
2. Implement required scoring methods.
3. Register strategy in the strategy registry.
4. Use its `strategyId` in a game or task.

---

## Integration Patterns

GAME can operate in two modes:

### 1. Full backend gamification platform

Use GAME as a complete gamification backend:

- manage games
- manage tasks
- assign points
- track wallets
- apply adaptive strategies

### 2. Scoring microservice

Use GAME only as an **incentive / scoring engine**:

- external system calls GAME to compute points
- GAME returns scoring outcome
- external system manages application logic

---

## Tech Stack

- Python ≥ 3.12
- FastAPI + Starlette
- SQLModel + SQLAlchemy
- PostgreSQL
- Poetry
- Docker / Docker Compose
- Kubernetes (`kubernetes/`)
- Keycloak OAuth2 / OpenID Connect

---

## Quick Start

> ⚡ **Just want it running?** The one-command Docker launchers in
> [Running with Docker](#running-with-docker) — `make dev` (Linux/macOS/WSL) or
> `.\start.ps1` (Windows) — bring up the whole stack. The steps below instead run
> the API directly with Poetry, which is handy for backend work without containers.

### Prerequisites

- Python + Poetry installed
- PostgreSQL running
- Keycloak (optional, required for protected endpoints)

### Clone

```bash
git clone https://github.com/fvergaracl/GAME.git
cd GAME
```

### Install

```bash
poetry install
```

### Configure

```bash
cp .env.sample .env
```

Minimal `.env`:

```env
ENV=dev
SECRET_KEY=change-me

DATABASE_URL=postgresql://root:example@localhost:5432/game_dev_db
ALEMBIC_DATABASE_URL=postgresql://root:example@localhost:5432/game_dev_db

KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=GameRealm
KEYCLOAK_CLIENT_ID=game-backend
KEYCLOAK_CLIENT_SECRET=change-me

# DB pool tuning (recommended for concurrent load)
SQLALCHEMY_ECHO=false
DB_POOL_PRE_PING=true
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT_SECONDS=30
DB_POOL_RECYCLE_SECONDS=1800
```

### Migrate DB

```bash
poetry run alembic upgrade head
```

### Run API

```bash
poetry run uvicorn app.main:app --reload
```

Docs:

- Swagger → [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc → [http://localhost:8000/redocs](http://localhost:8000/redocs)

---

## Keycloak OAuth (Dev)

Start the auth + database infrastructure:

```bash
docker-compose -f docker-compose-dev.yml up -d postgrespostgres keycloakgame
```

> The service names `postgrespostgres` and `keycloakgame` are intentional — they match `docker-compose-dev.yml`.

With the infrastructure running you can execute the full E2E suite (see [Tests & Coverage](#tests--coverage)). To exercise the auth flow manually:

```bash
TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=$KEYCLOAK_CLIENT_ID" \
  -d "client_secret=$KEYCLOAK_CLIENT_SECRET" \
  -d "grant_type=password" \
  -d "username=game_admin" \
  -d "password=$KEYCLOAK_USER_WITH_ROLE_PASSWORD" | jq -r '.access_token')
```

Create API key:

```bash
API_KEY=$(curl -s -X POST "http://localhost:8000/api/v1/apikey/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"client":"local-dev"}' | jq -r '.apiKey')
```

---

## API Example (End-to-End)

Create game → create task → assign points → read user score.

```bash
# Create game
GAME_ID=$(curl -s -X POST "http://localhost:8000/api/v1/games" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"externalGameId":"game-001","platform":"web","strategyId":"default"}' \
  | jq -r '.gameId')

# Create task
curl -s -X POST "http://localhost:8000/api/v1/games/$GAME_ID/tasks" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"externalTaskId":"task-login"}'

# Assign points
curl -s -X POST "http://localhost:8000/api/v1/games/$GAME_ID/tasks/task-login/points" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"externalUserId":"user-123"}'

# Read points
curl -s "http://localhost:8000/api/v1/users/user-123/points" \
  -H "X-API-Key: $API_KEY"
```

---

## Running with Docker

The fastest way to run the **entire stack** — API, PostgreSQL, Keycloak, dashboard, Prometheus and Grafana. The first run creates your `.env` from `.env.sample`, builds the images, and waits until the API is healthy (no prior `poetry install` needed).

**Linux / macOS / WSL** — use the `Makefile`:

```bash
make dev      # build + start the dev stack (creates .env on first run)
make logs     # tail logs (use make logs-api for just the API)
make down     # stop and remove containers
make clean    # stop and delete all data volumes (destructive)
```

**Windows** — use `start.ps1` from PowerShell (no Docker Desktop required; it can also drive Docker inside WSL2):

```powershell
.\start.ps1           # first run or normal start
.\start.ps1 -Logs     # start and follow logs
.\start.ps1 -Down     # stop services
.\start.ps1 -Force    # full rebuild
.\start.ps1 -Clean    # stop + delete data (asks for confirmation)
```

Once the stack is up:

| Service       | URL                                     |
| ------------- | --------------------------------------- |
| API (Swagger) | http://localhost:8000/docs              |
| Dashboard     | http://localhost:3000                   |
| Keycloak      | http://localhost:8080                   |
| Grafana       | http://localhost:3001 (`admin`/`admin`) |
| Prometheus    | http://localhost:9090                   |

<details>
<summary>Prefer plain Docker Compose?</summary>

```bash
docker-compose -f docker-compose-dev.yml up --build
docker-compose -f docker-compose-dev.yml down --remove-orphans
```

Integrated (Greengage) stack: `make integrated` then `make down`. See [SETUP.md](SETUP.md) for every Compose file and when to use each one.

</details>

---

## Tests & Coverage

```bash
poetry run pytest
poetry run pytest --cov=app --cov-branch
```

### Unit tests

```bash
# Recommended: one-command unit test runner
./scripts/run_unit_tests.sh

# Stop on first failure
./scripts/run_unit_tests.sh --fail-fast

# Coverage (branch + html report)
./scripts/run_unit_tests.sh --cov --cov-branch --cov-report html

# Run specific unit file
./scripts/run_unit_tests.sh --file tests/unit_tests/services/test_user_points_service.py

# Show all options
./scripts/run_unit_tests.sh --help
```

### E2E tests

```bash
# Recommended: one-command E2E runner (loads .env automatically)
./scripts/run_e2e.sh

# Include real-infrastructure E2E (requires API + PostgreSQL + Keycloak running)
./scripts/run_e2e.sh --real

# Same as above, but using .env.integrated
./scripts/run_e2e.sh --env-file .env.integrated --real

# Optional: direct pytest command for controlled E2E only
poetry run pytest tests/e2e -q -m "not e2e_real_http"

# Run a specific E2E test file
poetry run pytest tests/e2e/test_app_smoke_e2e.py -q

# Start E2E tests from a specific SQLite snapshot
poetry run pytest tests/e2e -q --e2e-base-snapshot /absolute/path/to/base_snapshot.sqlite

# Keep generated SQLite files for debugging
poetry run pytest tests/e2e -q --e2e-keep-db

# Run only real-infrastructure E2E for POST /apikey/create
./scripts/run_e2e.sh --real -- tests/e2e/test_apikey_create_flow_e2e.py -q
```

### Load tests (k6)

```bash
# Recommended: one-command load runner (loads .env automatically)
./scripts/run_load_test.sh

# Preset: 1000 VUs mode
./scripts/run_load_test.sh --mode 1000

# Custom N VUs + custom scenario mix (A/B/C) + durations
./scripts/run_load_test.sh \
  --vus 300 \
  --mix-a 60 --mix-b 30 --mix-c 10 \
  --warmup 20s --hold 2m --ramp-down 20s

# Use integrated env file
./scripts/run_load_test.sh --env-file .env.integrated --mode 100

# Show all options
./scripts/run_load_test.sh --help

# Pass extra native k6 args after '--'
./scripts/run_load_test.sh --mode 100 -- --http-debug=full

# Mitigate local EOF transport failures (stale keep-alive sockets)
./scripts/run_load_test.sh --mode 100 --no-vu-connection-reuse 1 --retry-transport-errors 1
```

Notes:

- Script: `tests/load/game_api_loadtest.js`
- Runner: `scripts/run_load_test.sh`
- Default write auth mode is `apikey` (set `--write-auth-mode bearer` to stress bearer path).
- Setup creates one game + 2 tasks + user pool, and teardown deletes the created game.
- If setup creates an API key, teardown revokes it via `DELETE /apikey/{prefix}` (admin bearer token), so the run cleans up after itself. A key supplied via `X_API_KEY` is left untouched.

---

## Project Structure

```
app/
 ├── api/          HTTP endpoints
 ├── core/         config, DI, DB
 ├── engine/       adaptive strategies
 ├── repository/   persistence layer
 ├── services/     business logic
 ├── model/        domain models
 └── util/         utilities
```

---

## Documentation

The full documentation is published as a **Sphinx site** (GitHub Pages, built
from [`docs/source/`](docs/source/) on every push to `main`) and is organized
along the [Diátaxis](https://diataxis.fr/) model - tutorials, how-to guides,
explanation, and reference. Every running instance also serves an interactive
API reference at `/docs` (Swagger UI) and `/redocs` (ReDoc).

**Start here, by goal** (all guides below live in [`docs/source/`](docs/source/)):

| I want to…                     | Read                                                                       |
| ------------------------------ | -------------------------------------------------------------------------- |
| Make my first API call         | `getting-started.rst` → `authentication.rst`                               |
| Integrate GAME into my product | `integrating.rst`, `strategies.rst`, `rest-api.rst`                        |
| Understand how it works        | `overview.rst`, `architecture.rst`, `dsl-engine.rst`, `domain-model.rst`   |
| Run it in production           | `configuration.rst`, `operations.rst`, `observability.rst`, `security.rst` |
| Contribute code or docs        | `architecture.rst`, `codebase.rst`, `contributing.rst`                     |

**Reference material:**

| Topic               | Document                                                                    |
| ------------------- | --------------------------------------------------------------------------- |
| Local setup         | [SETUP.md](SETUP.md)                                                        |
| Deployment          | [DEPLOYMENT.md](DEPLOYMENT.md) · [KUBERNETES_SETUP.md](KUBERNETES_SETUP.md) |
| Testing             | [TESTING.md](TESTING.md)                                                    |
| Strategy scenarios  | [strategies.md](strategies.md)                                              |
| Domain model (ERD)  | [docs/domain-model.md](docs/domain-model.md)                                |
| DSL block reference | [docs/dsl/](docs/dsl/) · [runbook](docs/dsl/runbook.md)                     |
| Troubleshooting     | [troubleshooting.md](troubleshooting.md)                                    |
| Contributing        | [CONTRIBUTING.md](CONTRIBUTING.md)                                          |

> Build the docs locally with `poetry run sphinx-build -b html docs/source _build/html`
> (or `poetry run sphinx-autobuild docs/source _build/html` for live preview).

---

## Production & Reliability

### Production considerations

- Use `ENV=prod` with secure secrets and externalized configuration.
- Run Alembic migrations in CI/CD before deployment.
- Enable structured logging for observability.
- Use connection pooling for PostgreSQL.
- GAME is stateless → supports horizontal scaling behind a load balancer.
- Manage secrets via environment variables or secret manager (not `.env` in prod).
- Sentry defaults are privacy-conservative (`SENTRY_SEND_DEFAULT_PII=false`, `SENTRY_TRACES_SAMPLE_RATE=0.1`, profiling off); opt in per env.
- Data retention / GDPR posture for the `logs` audit table is documented in [docs/DATA_RETENTION.md](docs/DATA_RETENTION.md).

### Failure modes & reliability

GAME is designed to behave safely under failure scenarios:

- **Idempotent operations** where applicable.
- Safe under **concurrent requests** with transactional DB behavior.
- Supports **retry-safe patterns**.
- Handles **partial failures** (service / DB exceptions).
- Authentication failure produces deterministic response (no silent fallback).
- Consistency model: **strong within transaction, eventual across distributed calls**.

### Python compatibility

- Poetry constraint: `python = "^3.12"` (effective range: `>=3.12,<4.0`)
- CI runs Python `3.12`
- Recommended local version: **Python 3.12.x**

---

## Reproducibility & Determinism

GAME is designed to support **scientific reproducibility and deterministic evaluation** of adaptive strategies.

To guarantee reproducible behavior:

- **Deterministic execution** - Given the same inputs (tasks, parameters, timestamps, and configuration), strategies produce identical outputs.
- **Explicit parameterization** - All scoring behavior is driven by explicit strategy parameters stored in the database, avoiding hidden state.
- **Simulation mode** - The engine supports simulation runs (`isSimulated=true`) to evaluate strategies without affecting production data.
- **Seeded stochastic components** - Any stochastic behavior (if used) should be seeded to allow repeatable experiments.
- **Stable time reference** - Strategies relying on time use controlled timestamps, enabling replay of historical scenarios.
- **Versionable strategies** - Strategy logic can be versioned, allowing comparison across experimental conditions.
- **Traceable execution** - Logs and scoring outputs allow reconstruction of scoring decisions for auditing and research validation.

These properties allow GAME to be used not only as an operational system, but also as a **reproducible experimental platform** for studying adaptive incentive mechanisms.

---

## Strategy Evaluation & Metrics

GAME enables systematic evaluation of adaptive gamification strategies through measurable outcomes.

Typical evaluation dimensions include:

### Participation Dynamics

- User participation rate
- Task completion distribution
- Retention and re-engagement patterns

### Incentive Redistribution

- Shift in activity across users or tasks
- Load balancing and participation equity
- Concentration vs dispersion metrics

### Behavioral Impact

- Response to adaptive incentives
- Performance improvement over baseline strategies
- Stability under changing participation conditions

### Spatial / Contextual Effects _(when applicable)_

- Redistribution across regions, zones, or task clusters
- Detection of hotspots and incentive-driven movement

### System Metrics

- Points issued over time
- Wallet balance evolution
- Strategy execution consistency

GAME can be used to compare:

- static vs adaptive strategies
- deterministic vs dynamic scoring
- baseline vs experimental incentive models

These evaluation capabilities make GAME suitable for **experimental research, adaptive systems validation, and real-world behavioral optimization studies**.

---

## Contributing & Community

**GAME is open source, and we'd love your help.** Whether you're fixing a typo,
reporting a bug, adding a scoring strategy, or improving the docs — every
contribution counts, and contributors of **all experience levels** are welcome.

### Ways to contribute

- 🐛 **Report a bug** or request a feature via [GitHub Issues](https://github.com/fvergaracl/GAME/issues).
- 🧩 **Add a strategy** — see [Adding a new strategy](#adding-a-new-strategy-minimal-steps) and `app/engine/`.
- 📝 **Improve the docs** — this README, the [Sphinx docs](docs/source/), or inline docstrings.
- ✅ **Write tests** — help us keep coverage above the **93%** gate.
- 💬 **Share ideas** or ask questions in [GitHub Discussions](https://github.com/fvergaracl/GAME/discussions).

### Your first contribution

New to the project? Browse issues labeled
[**good first issue**](https://github.com/fvergaracl/GAME/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22),
then follow the step-by-step guide in **[CONTRIBUTING.md](CONTRIBUTING.md)**. In short:

1. **Fork** the repo and create a feature branch.
2. **Install** with `poetry install` and set up the [pre-commit hooks](CONTRIBUTING.md#pre-commit-hooks-recommended).
3. **Make your change** with tests, then run `poetry run pytest` and the lint commands.
4. **Open a pull request** using the template — CI runs lint, tests, and the coverage gate.

By participating, you agree to uphold our **[Code of Conduct](CODE_OF_CONDUCT.md)**.
Found a security issue? Please follow the **[Security Policy](SECURITY.md)**
instead of opening a public issue.

---

## How to Cite GAME

If you use **GAME** in your research, academic work, or publications, please cite the software directly. This helps support the project and makes your results reproducible.

**Plain text:**

> Vergara-Borge, F (2025). _GAME (Goals And Motivation Engine): An adaptive gamification engine_. https://github.com/fvergaracl/GAME

**BibTeX:**

```bibtex
@software{vergara_game,
  author       = {Vergara-Borge, Felipe},
  title        = {{GAME}: Goals And Motivation Engine -- An Adaptive Gamification Engine},
  year         = {2025},
  publisher    = {GitHub},
  howpublished = {\url{https://github.com/fvergaracl/GAME}},
  url          = {https://github.com/fvergaracl/GAME}
}
```

If your work relates to a specific use case (citizen science, spatial crowdsourcing, or scalability), please also cite the corresponding paper listed under [Research & Publications](#research--publications) below.

---

## Research & Publications

GAME has been used and referenced in multiple research works on adaptive gamification, citizen science, and spatial crowdsourcing.

### Papers

**Enhancing Citizen Science Engagement Through Gamification: A Case Study of the SOCIO-BEE Project**  
Vergara, F., Olivares-Rodríguez, C., Guenaga, M., López-De-Ipiña, D., Puerta-Beldarrain, M., Sánchez-Corcuera, R.  
_9th International Conference on Smart and Sustainable Technologies (SpliTech), IEEE, 2024_  
Focus: Gamification-driven engagement mechanisms in citizen science using adaptive incentive structures.

```bibtex
@inproceedings{vergara2024enhancing,
  title={Enhancing Citizen Science Engagement Through Gamification: A Case Study of the SOCIO-BEE Project},
  author={Vergara, Felipe and Olivares-Rodr{\'\i}guez, Cristian and Guenaga, Mariluz and L{\'o}pez-De-Ipi{\~n}a, Diego and Puerta-Beldarrain, Maite and S{\'a}nchez-Corcuera, Rub{\'e}n},
  booktitle={2024 9th International Conference on Smart and Sustainable Technologies (SpliTech)},
  pages={1--7},
  year={2024},
  organization={IEEE}
}
```

---

**Gamifying Engagement in Spatial Crowdsourcing: An Exploratory Mixed-Methods Study on Gamification Impact among University Students**<br>
Vergara-Borge, F., López-de-Ipiña, D., Emaldi, M., Olivares-Rodríguez, C., Khan, Z., Soomro, K.<br>
_Systems, MDPI, 2025_<br>
Focus: Behavioral and participation effects of gamification in spatial crowdsourcing environments.

```bibtex
@article{vergara2025gamifying,
  title={Gamifying Engagement in Spatial Crowdsourcing: An Exploratory Mixed-Methods Study on Gamification Impact among University Students},
  author={Vergara-Borge, Felipe and L{\'o}pez-de-Ipi{\~n}a, Diego and Emaldi, Mikel and Olivares-Rodr{\'\i}guez, Cristian and Khan, Zaheer and Soomro, Kamran},
  journal={Systems},
  volume={13},
  number={7},
  pages={519},
  year={2025},
  publisher={MDPI}
}
```

---

**Stress-Testing Citizen Science at Scale: Performance Insights from the GREENCROWD Platform**<br>
Borge, F. V., López-de-Ipiña, D., Emaldi, M., Olivares-Rodríguez, C., Wolosiuk, D., Vuckovic, M.<br>
_10th International Conference on Smart and Sustainable Technologies (SpliTech), IEEE, 2025_<br>
Focus: Scalability, system performance, and large-scale participation behavior in adaptive citizen science platforms.

```bibtex
@inproceedings{borge2025stress,
  title={Stress-Testing Citizen Science at Scale: Performance Insights from the GREENCROWD Platform},
  author={Borge, Felipe Vergara and L{\'o}pez-de-Ipi{\~n}a, Diego and Manrique, Mikel Emaldi and Olivares-Rodr{\'\i}guez, Cristian and Wolosiuk, Dawid and Vuckovic, Milena},
  booktitle={2025 10th International Conference on Smart and Sustainable Technologies (SpliTech)},
  pages={1--8},
  year={2025},
  organization={IEEE}
}
```

---

These works demonstrate the use of GAME in **adaptive gamification, behavioral incentive shaping, spatial crowdsourcing, and citizen science systems**, supporting both experimental research and real-world deployments.

---

## License

GAME is released under the **[Apache License 2.0](LICENSE)** — free to use,
modify, and distribute, including commercially, provided you retain the license
and attribution.

---

## Contact & Support

- 🐛 **Bugs & features** → [GitHub Issues](https://github.com/fvergaracl/GAME/issues)
- 💬 **Questions & ideas** → [GitHub Discussions](https://github.com/fvergaracl/GAME/discussions)
- 🔒 **Security reports** → see [SECURITY.md](SECURITY.md)
- 📧 **Maintainer** → Felipe Vergara-Borge ([felipe.vergara@deusto.es](mailto:felipe.vergara@deusto.es))

If GAME is useful to you, please consider ⭐ starring the repo and
[citing it](#how-to-cite-game) in your work.
