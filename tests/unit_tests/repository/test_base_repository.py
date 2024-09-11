import pytest
from dependency_injector import containers, providers
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import DuplicatedError, NotFoundError
from app.repository.base_repository import BaseRepository

Base = declarative_base()


class Model(Base):
    __tablename__ = "test_model"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=True)


class ModelSchema(BaseModel):
    name: str
    value: str = None

    class Config:
        orm_mode = True


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    db = providers.Singleton(create_engine, "sqlite:///:memory:", echo=True)
    session_factory = providers.Factory(sessionmaker, bind=db)
    test_repository = providers.Factory(
        BaseRepository, session_factory=session_factory, model=Model
    )


@pytest.fixture(scope="module")
def container():
    return Container()


@pytest.fixture(scope="function")
def setup_database(container):
    engine = container.db()
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def repository(container, setup_database):
    return container.test_repository()


# Pruebas


def test_create(repository):
    schema = ModelSchema(name="test", value="value")
    created = repository.create(schema)
    assert created.id is not None
    assert created.name == "test"


def test_read_by_id(repository):
    schema = ModelSchema(name="test_read", value="value")
    created = repository.create(schema)
    found = repository.read_by_id(created.id)
    assert found.id == created.id
    assert found.name == "test_read"


def test_update(repository):
    schema = ModelSchema(name="test_update", value="value")
    created = repository.create(schema)
    update_schema = ModelSchema(name="test_update", value="new_value")
    updated = repository.update(created.id, update_schema)
    assert updated.value == "new_value"


def test_delete(repository):
    schema = ModelSchema(name="test_delete", value="value")
    created = repository.create(schema)
    repository.delete_by_id(created.id)
    with pytest.raises(NotFoundError):
        repository.read_by_id(created.id)


def test_read_by_column(repository):
    schema1 = ModelSchema(name="test_column_1", value="value1")
    schema2 = ModelSchema(name="test_column_2", value="value2")
    repository.create(schema1)
    repository.create(schema2)
    result = repository.read_by_column("name", "test_column_1")
    assert result.name == "test_column_1"


def test_duplicate_error(repository):
    schema1 = ModelSchema(name="unique_name", value="value1")
    schema2 = ModelSchema(name="unique_name", value="value2")
    repository.create(schema1)
    with pytest.raises(DuplicatedError):
        repository.create(schema2)


def test_not_found_error(repository):
    with pytest.raises(NotFoundError):
        repository.read_by_id(999)


def test_update_attr(repository):
    schema = ModelSchema(name="test_attr", value="value")
    created = repository.create(schema)
    repository.update_attr(created.id, "value", "new_value")
    updated = repository.read_by_id(created.id)
    assert updated.value == "new_value"


def test_whole_update(repository):
    schema = ModelSchema(name="test_whole", value="value")
    created = repository.create(schema)
    update_schema = ModelSchema(name="updated_name", value="updated_value")
    updated = repository.whole_update(created.id, update_schema)
    assert updated.name == "updated_name"
    assert updated.value == "updated_value"
