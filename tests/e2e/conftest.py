import os
import shutil
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Dict, Optional

import pytest
import pytest_asyncio
from dependency_injector import providers
from httpx import AsyncClient
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
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
    Async database wrapper used by E2E tests. Mirrors the interface of
    :class:`app.core.database.Database` (``async with db.session() as s``) so
    repository providers see the same contract as in production.
    """

    def __init__(self, db_url: str):
        self._engine = create_async_engine(db_url, future=True)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def create_all(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        session: AsyncSession = self._session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def dispose(self) -> None:
        await self._engine.dispose()


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


async def _initialize_database(
    db_path: Path,
    base_state: str,
    base_snapshot: Optional[Path],
) -> ControlledDatabase:
    if base_snapshot:
        if not base_snapshot.exists():
            raise FileNotFoundError(f"E2E base snapshot not found: {base_snapshot}")
        shutil.copy2(base_snapshot, db_path)

    db = ControlledDatabase(f"sqlite+aiosqlite:///{db_path}")

    if base_snapshot is None:
        await db.create_all()

    if base_state != "empty":
        raise ValueError(f"Unsupported E2E base state: {base_state}. Supported: empty")

    return db


@pytest_asyncio.fixture
async def e2e_context(tmp_path: Path, request: pytest.FixtureRequest, e2e_runtime):
    app, container = e2e_runtime
    base_state = _resolve_base_state(request)
    base_snapshot = _resolve_base_snapshot(request)
    keep_db = bool(request.config.getoption("--e2e-keep-db"))

    db_path = tmp_path / "e2e.sqlite3"
    db = await _initialize_database(
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
        await db.dispose()
        if not keep_db and db_path.exists():
            db_path.unlink()


@pytest_asyncio.fixture
async def e2e_client(e2e_context: E2EContext):
    async with AsyncClient(app=e2e_context.app, base_url="http://testserver") as client:
        yield client
