from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import as_declarative, declared_attr


@as_declarative()
class BaseModel:
    """
    Base model class for SQLAlchemy ORM models.

    Attributes:
        id (Any): The primary key of the model.
        __name__ (str): The name of the model class.
    """

    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


def _to_async_url(db_url: str) -> str:
    """
    Coerce a sync DB URL into the async-driver form. Allows operators to keep
    the sync-style ``DATABASE_URI`` in env files while the engine itself runs
    on asyncpg / aiosqlite.
    """
    url = make_url(db_url)
    backend = url.get_backend_name()
    driver = url.get_driver_name() or ""
    if backend == "postgresql" and driver in ("", "psycopg2", "psycopg"):
        return url.set(drivername="postgresql+asyncpg").render_as_string(
            hide_password=False
        )
    if backend == "sqlite" and driver in ("", "pysqlite"):
        return url.set(drivername="sqlite+aiosqlite").render_as_string(
            hide_password=False
        )
    if backend == "mysql" and driver in ("", "pymysql", "mysqldb"):
        return url.set(drivername="mysql+aiomysql").render_as_string(
            hide_password=False
        )
    return db_url


class Database:
    """
    Async database wrapper around SQLAlchemy 2.0's ``AsyncEngine`` and
    ``async_sessionmaker``. Exposes an ``async with database.session() as s``
    context manager used by every repository.
    """

    def __init__(
        self,
        db_url: str,
        *,
        echo: bool = False,
        pool_pre_ping: bool = True,
        pool_size: int = 20,
        max_overflow: int = 40,
        pool_timeout_seconds: int = 30,
        pool_recycle_seconds: int = 1800,
    ) -> None:
        async_url = _to_async_url(db_url)
        engine_kwargs: dict = {"echo": echo}
        if make_url(async_url).get_backend_name() != "sqlite":
            engine_kwargs.update(
                {
                    "pool_pre_ping": pool_pre_ping,
                    "pool_size": max(1, int(pool_size)),
                    "max_overflow": max(0, int(max_overflow)),
                    "pool_timeout": max(1, int(pool_timeout_seconds)),
                    "pool_recycle": max(30, int(pool_recycle_seconds)),
                }
            )

        self._engine = create_async_engine(async_url, **engine_kwargs)
        self._session_factory: Callable[..., AsyncSession] = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def create_database(self) -> None:
        """
        Create all tables declared on the metadata if they do not yet exist.

        Runs ``BaseModel.metadata.create_all`` inside a transactional
        connection. Intended for bootstrapping local/test databases;
        production schema changes go through migrations.
        """
        async with self._engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Yield a managed ``AsyncSession`` for a unit of work.

        The session is rolled back automatically if the wrapped block raises,
        and is always closed on exit. Used as ``async with database.session()
        as s:`` by every repository.

        Yields:
            AsyncSession: An active database session bound to the engine.
        """
        session: AsyncSession = self._session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
