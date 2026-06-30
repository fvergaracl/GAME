# Testing

The testing workflow and the coverage gate are documented in one place - the
[contributing](docs/source/contributing.rst) guide - so this file is only a
pointer.

```bash
poetry run pytest      # full suite; CI enforces a hard, blocking coverage gate
```

The layered suite (unit / E2E controlled / E2E real infra / k6 load), the
one-command runners under `scripts/run_*`, and the coverage gate all live in
[contributing](docs/source/contributing.rst).
