# Setup

GAME is a **FastAPI** service (Python 3.12+, PostgreSQL, optional Keycloak for
OAuth2). Setup and first-run instructions are maintained in one place - the
Sphinx documentation - so this file is only a pointer.

- **One-command stack** (API + PostgreSQL + Keycloak + dashboard +
  observability): `make dev` on Linux/macOS/WSL, or `.\start.ps1` on Windows.
  See the [README quick start](README.md#quick-start).
- **Step-by-step setup** (Docker Compose *and* local Poetry, end to end):
  [getting-started](docs/source/getting-started.rst).
- **Every environment variable**:
  [configuration](docs/source/configuration.rst). The real values live in
  [`.env.sample`](.env.sample).
- **Compose files, Kubernetes, and deployment**:
  [operations](docs/source/operations.rst), [DEPLOYMENT.md](DEPLOYMENT.md), and
  [KUBERNETES_SETUP.md](KUBERNETES_SETUP.md).
- **Troubleshooting the first run**:
  [troubleshooting](docs/source/troubleshooting.rst).
