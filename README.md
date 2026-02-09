# GAME (Goals And Motivation Engine)

<p align="center">
  <img src="https://codecov.io/gh/fvergaracl/GAME/branch/main/graph/badge.svg?token=R0MGAOMUBU" alt="Codecov">
  <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License Apache 2.0">
  <img src="https://img.shields.io/github/stars/fvergaracl/GAME" alt="GitHub Repo stars">
  <img src="https://img.shields.io/github/v/tag/fvergaracl/game?color=green" alt="Last tag">
</p>

<p align="center">
  <img src="GAME_logo.png" alt="GAME Logo">
</p>

GAME is an **adaptive gamification engine** designed to dynamically shape participation, incentives, and behavioral outcomes through programmable scoring strategies. It exposes APIs to manage games, tasks, point assignment, wallets, and strategy-driven scoring behavior.

---

# What problem does GAME solve

Most gamification systems are **static**: rules and rewards are fixed, producing predictable engagement patterns and often reinforcing participation inequality.

GAME introduces **adaptive gamification**, enabling:

- **Adaptive vs static gamification**: scoring rules can react to behavior, context, or system state.
- **Behavioral redistribution**: incentives can shift participation toward under-engaged users, tasks, or areas.
- **Spatial / incentive shaping**: strategies can modify rewards dynamically based on distribution, performance, or context.
- **Equity / participation optimization**: reward structures can balance participation instead of amplifying inequality.

GAME is designed as a **programmable incentive engine**, not just a points API.

---

# Architecture Overview

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

# Strategy Model (Core Feature)

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

# Integration Pattern

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

# Production Considerations

- Use `ENV=prod` with secure secrets and externalized configuration.
- Run Alembic migrations in CI/CD before deployment.
- Enable structured logging for observability.
- Use connection pooling for PostgreSQL.
- GAME is stateless → supports horizontal scaling behind a load balancer.
- Manage secrets via environment variables or secret manager (not `.env` in prod).

---

# Failure Modes & Reliability

GAME is designed to behave safely under failure scenarios:

- **Idempotent operations** where applicable.
- Safe under **concurrent requests** with transactional DB behavior.
- Supports **retry-safe patterns**.
- Handles **partial failures** (service / DB exceptions).
- Authentication failure produces deterministic response (no silent fallback).
- Consistency model: **strong within transaction, eventual across distributed calls**.

---

# Python Compatibility

- Poetry constraint: `python = "^3.10"` (effective range: `>=3.10,<4.0`)
- CI currently runs Python `3.12.3`
- Recommended local version: **Python 3.12.x**

---

# Stack

- Python ≥ 3.10
- FastAPI + Starlette
- SQLModel + SQLAlchemy
- PostgreSQL
- Poetry
- Docker / Docker Compose
- Kubernetes (`kubernetes/`)
- Keycloak OAuth2 / OpenID Connect

---

# Quick Start (Local)

## Prerequisites

- Python + Poetry installed
- PostgreSQL running
- Keycloak (optional, required for protected endpoints)

## Clone

```bash
git clone https://github.com/fvergaracl/GAME.git
cd GAME
```

## Install

```bash
poetry install
```

## Configure

```bash
cp .env.sample .env
```

Minimal `.env`:

```env
ENV=dev
SECRET_KEY=change-me

DATABASE_URL=postgresql+psycopg2://root:example@localhost:5432/game_dev_db
ALEMBIC_DATABASE_URL=postgresql+psycopg2://root:example@localhost:5432/game_dev_db

KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=game
KEYCLOAK_CLIENT_ID=game-api
KEYCLOAK_CLIENT_SECRET=change-me
```

## Migrate DB

```bash
poetry run alembic upgrade head
```

## Run API

```bash
poetry run uvicorn app.main:app --reload
```

Docs:

- Swagger → [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc → [http://localhost:8000/redocs](http://localhost:8000/redocs)

---

# Keycloak OAuth (Dev)

Start infra:

```bash
docker-compose -f docker-compose-dev.yml up -d postgrespostgres keycloakgame
```

Get token:

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

# API Example (End-to-End)

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

# Docker

```bash
docker-compose -f docker-compose-dev.yml up --build
docker-compose -f docker-compose-dev.yml down --remove-orphans
```

Integrated:

```bash
make integrated
make down
```

---

# Tests & Coverage

```bash
poetry run pytest
poetry run pytest --cov=app --cov-branch
```

---

# Project Structure

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

# Documentation

- SETUP.md
- TESTING.md
- DEPLOYMENT.md
- KUBERNETES_SETUP.md
- strategies.md
- troubleshooting.md
- CONTRIBUTING.md

---

## Reproducibility & Determinism

GAME is designed to support **scientific reproducibility and deterministic evaluation** of adaptive strategies.

To guarantee reproducible behavior:

- **Deterministic execution** — Given the same inputs (tasks, parameters, timestamps, and configuration), strategies produce identical outputs.
- **Explicit parameterization** — All scoring behavior is driven by explicit strategy parameters stored in the database, avoiding hidden state.
- **Simulation mode** — The engine supports simulation runs (`isSimulated=true`) to evaluate strategies without affecting production data.
- **Seeded stochastic components** — Any stochastic behavior (if used) should be seeded to allow repeatable experiments.
- **Stable time reference** — Strategies relying on time use controlled timestamps, enabling replay of historical scenarios.
- **Versionable strategies** — Strategy logic can be versioned, allowing comparison across experimental conditions.
- **Traceable execution** — Logs and scoring outputs allow reconstruction of scoring decisions for auditing and research validation.

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

**Gamifying Engagement in Spatial Crowdsourcing: An Exploratory Mixed-Methods Study on Gamification Impact among University Students**
Vergara-Borge, F., López-de-Ipiña, D., Emaldi, M., Olivares-Rodríguez, C., Khan, Z., Soomro, K.
_Systems, MDPI, 2025_
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

**Stress-Testing Citizen Science at Scale: Performance Insights from the GREENCROWD Platform**
Borge, F. V., López-de-Ipiña, D., Emaldi, M., Olivares-Rodríguez, C., Wolosiuk, D., Vuckovic, M.
_10th International Conference on Smart and Sustainable Technologies (SpliTech), IEEE, 2025_
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

# License

Apache 2.0

---

# Contact

Open an issue: [https://github.com/fvergaracl/GAME/issues](https://github.com/fvergaracl/GAME/issues)
