from contextlib import AbstractContextManager, contextmanager
from typing import Any, Callable

from sqlalchemy import create_engine, orm
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

    def __init__(self, db_url: str) -> None:
        """
        Initializes the Database with the provided database URL.

        Args:
            db_url (str): The database URL.
        """
        self._engine = create_engine(db_url, echo=True)
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
