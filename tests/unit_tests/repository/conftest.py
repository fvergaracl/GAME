"""
Async-aiosqlite integration test infrastructure for the repository layer.

The legacy repository tests targeted a sync ``session.query()`` API that no
longer exists; the SQLAlchemy 2.0 async session uses
``await session.execute(select(...))`` everywhere. Rather than re-mocking that
chain (brittle, low-value), tests in this directory run the real repositories
against an in-memory aiosqlite database, with a Postgres -> SQLite shim for
``UUID``/``JSONB`` column types so the production model definitions can be
created untouched.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlmodel import SQLModel

import app.model.abuse_limit_counter  # noqa: F401
import app.model.api_key  # noqa: F401
import app.model.api_requests  # noqa: F401
import app.model.game_params  # noqa: F401
import app.model.games  # noqa: F401
import app.model.kpi_metrics  # noqa: F401
import app.model.logs  # noqa: F401
import app.model.oauth_users  # noqa: F401
import app.model.task_params  # noqa: F401
import app.model.tasks  # noqa: F401
import app.model.uptime_logs  # noqa: F401
import app.model.user_actions  # noqa: F401
import app.model.user_game_config  # noqa: F401
import app.model.user_interactions  # noqa: F401
import app.model.user_points  # noqa: F401
import app.model.users  # noqa: F401
import app.model.wallet  # noqa: F401
import app.model.wallet_transactions  # noqa: F401


@compiles(PG_UUID, "sqlite")
def _compile_uuid_for_sqlite(_type, _compiler, **_kw):
    return "CHAR(36)"


@compiles(PG_JSONB, "sqlite")
def _compile_jsonb_for_sqlite(_type, _compiler, **_kw):
    return "JSON"


@pytest_asyncio.fixture
async def async_engine():
    """
    Brand-new in-memory aiosqlite engine + schema per test. Using a fresh
    engine (rather than reusing one with TRUNCATE) keeps tests fully isolated
    and avoids cross-test state leaks via FK references.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(async_engine):
    """
    Returns a callable matching the repository constructor's expected
    ``Callable[..., AbstractAsyncContextManager[AsyncSession]]`` signature.
    """
    sessionmaker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    @asynccontextmanager
    async def _factory() -> AsyncIterator[AsyncSession]:
        session: AsyncSession = sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    return _factory


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncIterator[AsyncSession]:
    """
    A single AsyncSession for tests that want to seed data directly without
    going through a repository.
    """
    sessionmaker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    session = sessionmaker()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture
def asyncmock_session_factory():
    """
    Factory helper for tests that need a fully mocked async session — used by
    cases that exercise postgres-only code paths (``ON CONFLICT DO UPDATE``)
    which aiosqlite cannot execute as-is.
    """
    from contextlib import asynccontextmanager
    from unittest.mock import AsyncMock, MagicMock

    def _make():
        session = MagicMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()

        @asynccontextmanager
        async def _factory():
            yield session

        return _factory, session

    return _make
