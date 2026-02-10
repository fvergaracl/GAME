from contextlib import AbstractContextManager, contextmanager
from typing import Any, Callable

from sqlalchemy import create_engine, orm
from sqlalchemy.engine import make_url
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session


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

    @declared_attr  # noqa
    def __tablename__(cls) -> str:
        """
        Automatically generates the table name from the model class name.

        Returns:
            str: The table name.
        """
        return cls.__name__.lower()


class Database:
    """
    Database class for managing SQLAlchemy sessions and engine.

    Attributes:
        _engine: SQLAlchemy engine instance.
        _session_factory: SQLAlchemy session factory.
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
        """
        Initializes the Database with the provided database URL.

        Args:
            db_url (str): The database URL.
        """
        engine_kwargs = {"echo": echo}
        dialect_name = make_url(db_url).get_backend_name()
        if dialect_name != "sqlite":
            engine_kwargs.update(
                {
                    "pool_pre_ping": pool_pre_ping,
                    "pool_size": max(1, int(pool_size)),
                    "max_overflow": max(0, int(max_overflow)),
                    "pool_timeout": max(1, int(pool_timeout_seconds)),
                    "pool_recycle": max(30, int(pool_recycle_seconds)),
                }
            )

        self._engine = create_engine(db_url, **engine_kwargs)
        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            ),
        )

    def create_database(self) -> None:  # noqa
        """
        Creates the database tables defined in the BaseModel metadata.

        Returns:
            None
        """
        BaseModel.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Callable[..., AbstractContextManager[Session]]:
        """
        Provides a context manager for a SQLAlchemy session.

        Yields:
            Session: A SQLAlchemy session.
        """
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
