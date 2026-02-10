import os
import shutil
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, Optional

import pytest
from dependency_injector import providers
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy import create_engine, orm
from sqlalchemy.orm import Session
from sqlmodel import SQLModel


@compiles(PG_UUID, "sqlite")
def _compile_uuid_for_sqlite(_type, _compiler, **_kw):
    # E2E sqlite compatibility for postgres UUID columns.
    return "CHAR(36)"


@compiles(PG_JSONB, "sqlite")
def _compile_jsonb_for_sqlite(_type, _compiler, **_kw):
    # E2E sqlite compatibility for postgres JSONB columns.
    return "JSON"


def _env_flag(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class ControlledDatabase:
    """
    Lightweight database wrapper used by E2E tests.

    It mirrors the interface expected by repository providers (`session()`).
    """

    def __init__(self, db_url: str):
        self._engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            )
        )

    @contextmanager
    def session(self) -> Iterator[Session]:
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self._session_factory.remove()
        self._engine.dispose()


@dataclass
class E2EContext:
    app: object
    container: object
    db_path: Path
    base_state: str
    base_snapshot: Optional[Path]


def pytest_addoption(parser):
    group = parser.getgroup("e2e")
    group.addoption(
        "--e2e-base-state",
        action="store",
        default=os.getenv("E2E_BASE_STATE", "empty"),
        help="Initial state for E2E DB. Currently supported: empty",
    )
    group.addoption(
        "--e2e-base-snapshot",
        action="store",
        default=os.getenv("E2E_BASE_SNAPSHOT", ""),
        help="Path to a SQLite snapshot file used as E2E starting point.",
    )
    group.addoption(
        "--e2e-keep-db",
        action="store_true",
        default=_env_flag(os.getenv("E2E_KEEP_DB"), default=False),
        help="Keep generated E2E sqlite files after tests finish.",
    )


@pytest.fixture(scope="session", autouse=True)
def _preserve_environment():
    original_env: Dict[str, str] = dict(os.environ)
    os.environ["SENTRY_DSN"] = ""
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="session")
def e2e_runtime():
    # Imported lazily so environment tweaks are already in place.
    from app.main import app, container

    return app, container


def _resolve_base_state(request: pytest.FixtureRequest) -> str:
    marker = request.node.get_closest_marker("e2e_base_state")
    if marker and marker.args:
        return str(marker.args[0])
    return str(request.config.getoption("--e2e-base-state"))


def _resolve_base_snapshot(request: pytest.FixtureRequest) -> Optional[Path]:
    marker = request.node.get_closest_marker("e2e_base_snapshot")
    if marker and marker.args:
        return Path(str(marker.args[0])).expanduser().resolve()
    cli_value = str(request.config.getoption("--e2e-base-snapshot")).strip()
    if not cli_value:
        return None
    return Path(cli_value).expanduser().resolve()


def _initialize_database(
    db_path: Path,
    base_state: str,
    base_snapshot: Optional[Path],
) -> ControlledDatabase:
    if base_snapshot:
        if not base_snapshot.exists():
            raise FileNotFoundError(
                f"E2E base snapshot not found: {base_snapshot}"
            )
        shutil.copy2(base_snapshot, db_path)

    db = ControlledDatabase(f"sqlite:///{db_path}")

    if base_snapshot is None:
        SQLModel.metadata.drop_all(db._engine)
        SQLModel.metadata.create_all(db._engine)

    if base_state != "empty":
        raise ValueError(
            f"Unsupported E2E base state: {base_state}. Supported: empty"
        )

    return db


@pytest.fixture
def e2e_context(tmp_path: Path, request: pytest.FixtureRequest, e2e_runtime):
    app, container = e2e_runtime
    base_state = _resolve_base_state(request)
    base_snapshot = _resolve_base_snapshot(request)
    keep_db = bool(request.config.getoption("--e2e-keep-db"))

    db_path = tmp_path / "e2e.sqlite3"
    db = _initialize_database(
        db_path=db_path,
        base_state=base_state,
        base_snapshot=base_snapshot,
    )

    previous_dependency_overrides = dict(app.dependency_overrides)
    container.db.override(providers.Object(db))
    app.dependency_overrides.clear()

    try:
        yield E2EContext(
            app=app,
            container=container,
            db_path=db_path,
            base_state=base_state,
            base_snapshot=base_snapshot,
        )
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_dependency_overrides)
        container.db.reset_override()
        db.dispose()
        if not keep_db and db_path.exists():
            db_path.unlink()


@pytest.fixture
def e2e_client(e2e_context: E2EContext):
    with TestClient(e2e_context.app) as client:
        yield client
