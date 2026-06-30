#!/usr/bin/env python3
"""Anti-drift guard for the GAME documentation.

The docs and the code drifted apart once before (a stale realm name broke the
first-run guide, a quick-start curl-ed an endpoint that no longer existed). This
script makes that class of drift a CI failure instead of a reader's problem.

Two checks, both run on every push/PR by ``.github/workflows/docs-drift.yml``:

A. **Env-var identity drift** - a curated set of *identity* variables (the
   Keycloak realm/client/audience) must read the same in the ``.rst`` docs as
   in ``.env.sample``, which is the source of truth (the realm template is
   rendered from those vars). Secrets (``*_SECRET``, passwords) and
   environment-specific hosts (``DB_HOST``, ``KEYCLOAK_URL``) legitimately
   differ between a dev sample and a prod example, so they are deliberately
   *not* enforced - extend ``ENFORCED_VARS`` only with values that must be
   identical everywhere.

B. **Quick-start endpoint drift** - every ``/api/v1/...`` URL the getting-started
   guide tells a newcomer to curl must exist as a path in the live OpenAPI
   schema (``app.openapi()``). A documented endpoint that the app does not serve
   fails the build.

Run locally with::

    ENV=test poetry run python scripts/check_docs_drift.py
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Run from anywhere: make the ``app`` package importable for the OpenAPI check
# (when invoked as a file, sys.path[0] is scripts/, not the repo root).
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DOCS_SOURCE = REPO_ROOT / "docs" / "source"
ENV_SAMPLE = REPO_ROOT / ".env.sample"
QUICKSTART = DOCS_SOURCE / "getting-started.rst"

# Identity values that must be identical in the docs and in .env.sample. These
# are exactly the variables whose divergence broke first-run auth before
# (the realm template is rendered from them). Keep this list tight: only add a
# variable when every place that mentions it must agree on the value.
ENFORCED_VARS = (
    "KEYCLOAK_REALM",
    "KEYCLOAK_CLIENT_ID",
    "KEYCLOAK_AUDIENCE",
)

_ASSIGN_RE = re.compile(r"^\s*([A-Z][A-Z0-9_]+)\s*=\s*(.+?)\s*$")
_URL_RE = re.compile(r"http://localhost:8000(/[^\s\"'\\]*)")


def _clean_value(raw: str) -> str:
    """Strip an inline ``# comment`` and surrounding quotes from a value."""
    value = re.split(r"\s+#", raw, maxsplit=1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def _parse_env_sample() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in ENV_SAMPLE.read_text().splitlines():
        match = _ASSIGN_RE.match(line)
        if match:
            values[match.group(1)] = _clean_value(match.group(2))
    return values


def check_env_drift() -> list[str]:
    """Return a list of human-readable drift problems (empty == clean)."""
    sample = _parse_env_sample()
    problems: list[str] = []

    missing = [v for v in ENFORCED_VARS if v not in sample]
    if missing:
        problems.append(
            f".env.sample is missing enforced variable(s): {', '.join(missing)}"
        )

    for rst in sorted(DOCS_SOURCE.glob("*.rst")):
        for lineno, line in enumerate(rst.read_text().splitlines(), start=1):
            match = _ASSIGN_RE.match(line)
            if not match:
                continue
            name, raw = match.group(1), match.group(2)
            if name not in ENFORCED_VARS or name not in sample:
                continue
            doc_value = _clean_value(raw)
            expected = sample[name]
            if doc_value != expected:
                rel = rst.relative_to(REPO_ROOT)
                problems.append(
                    f"{rel}:{lineno}: {name}={doc_value!r} "
                    f"but .env.sample has {expected!r}"
                )
    return problems


def _api_base() -> str:
    """The path prefix the public API is mounted under (default /api/v1)."""
    try:
        from app.core.config import configs

        return getattr(configs, "API_V1_STR", "/api/v1")
    except Exception:  # pragma: no cover - fall back to the documented default
        return "/api/v1"


def _openapi_paths() -> set[str]:
    from app.main import app

    return set(app.openapi().get("paths", {}).keys())


def _path_is_covered(doc_path: str, templates: set[str]) -> bool:
    """True if ``doc_path`` matches an OpenAPI path template segment-for-segment.

    A ``{param}`` template segment matches any single concrete segment (a shell
    variable like ``$GAME_ID`` or a literal id like ``task-login``); literal
    segments must match exactly.
    """
    doc_segs = [s for s in doc_path.split("/") if s]
    for tmpl in templates:
        t_segs = [s for s in tmpl.split("/") if s]
        if len(t_segs) != len(doc_segs):
            continue
        if all(
            (t.startswith("{") and t.endswith("}")) or t == d
            for d, t in zip(doc_segs, t_segs)
        ):
            return True
    return False


def check_quickstart_endpoints() -> list[str]:
    """Every /api/v1 URL in the quick-start must exist in the OpenAPI schema."""
    base = _api_base()
    try:
        templates = _openapi_paths()
    except Exception as exc:  # surfacing the import failure is the point
        return [f"could not load the OpenAPI schema (app.openapi()): {exc}"]

    problems: list[str] = []
    seen: set[str] = set()
    for lineno, line in enumerate(QUICKSTART.read_text().splitlines(), start=1):
        for full_path in _URL_RE.findall(line):
            if not full_path.startswith(base + "/"):
                continue  # non-API URL (/docs, /redocs, /metrics, bare host)
            rel_path = full_path[len(base) :]
            key = f"{rel_path}"
            if key in seen:
                continue
            seen.add(key)
            if not _path_is_covered(rel_path, templates):
                problems.append(
                    f"{QUICKSTART.relative_to(REPO_ROOT)}:{lineno}: quick-start "
                    f"curls {base}{rel_path}, which is not in the OpenAPI schema"
                )
    return problems


def main() -> int:
    os.environ.setdefault("ENV", "test")
    env_problems = check_env_drift()
    api_problems = check_quickstart_endpoints()

    if env_problems:
        print("Env-var drift (docs vs .env.sample):")
        for problem in env_problems:
            print(f"  - {problem}")
    if api_problems:
        print("Quick-start endpoint drift (docs vs OpenAPI):")
        for problem in api_problems:
            print(f"  - {problem}")

    if env_problems or api_problems:
        print(
            "\nDocs drift detected. Fix the docs (or .env.sample / the API) so "
            "they agree, then re-run: poetry run python scripts/check_docs_drift.py"
        )
        return 1

    print("Docs drift guard: OK (env identity values and quick-start endpoints match).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
