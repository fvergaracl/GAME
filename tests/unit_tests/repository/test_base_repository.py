from types import SimpleNamespace
from unittest.mock import MagicMock

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


class DummySchema:
    def __init__(self, payload):
        self.payload = payload

    def dict(self, exclude_none=False):
        if exclude_none:
            return {k: v for k, v in self.payload.items() if v is not None}
        return dict(self.payload)


def build_mocked_repository():
    mock_session = MagicMock()
    context_manager = MagicMock()
    context_manager.__enter__.return_value = mock_session
    context_manager.__exit__.return_value = False
    session_factory = MagicMock(return_value=context_manager)
    repository = BaseRepository(session_factory=session_factory, model=Model)
    return repository, mock_session


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


@pytest.mark.asyncio
async def test_create(repository):
    schema = ModelSchema(name="test", value="value")
    created = await repository.create(schema)
    assert created.id is not None
    assert created.name == "test"


@pytest.mark.asyncio
async def test_read_by_id(repository):
    schema = ModelSchema(name="test_read", value="value")
    created = await repository.create(schema)
    found = repository.read_by_id(created.id)
    assert found.id == created.id
    assert found.name == "test_read"


@pytest.mark.asyncio
async def test_update(repository):
    schema = ModelSchema(name="test_update", value="value")
    created = await repository.create(schema)
    update_schema = ModelSchema(name="test_update", value="new_value")
    updated = await repository.update(created.id, update_schema)
    assert updated.value == "new_value"


@pytest.mark.asyncio
async def test_delete(repository):
    schema = ModelSchema(name="test_delete", value="value")
    created = await repository.create(schema)
    repository.delete_by_id(created.id)
    with pytest.raises(NotFoundError):
        repository.read_by_id(created.id)


@pytest.mark.asyncio
async def test_read_by_column(repository):
    schema1 = ModelSchema(name="test_column_1", value="value1")
    schema2 = ModelSchema(name="test_column_2", value="value2")
    await repository.create(schema1)
    await repository.create(schema2)
    result = repository.read_by_column("name", "test_column_1")
    assert result.name == "test_column_1"


@pytest.mark.asyncio
async def test_duplicate_error(repository):
    schema1 = ModelSchema(name="unique_name", value="value1")
    schema2 = ModelSchema(name="unique_name", value="value2")
    await repository.create(schema1)
    with pytest.raises(DuplicatedError):
        await repository.create(schema2)


def test_not_found_error(repository):
    with pytest.raises(NotFoundError):
        repository.read_by_id(999)


@pytest.mark.asyncio
async def test_update_attr(repository):
    schema = ModelSchema(name="test_attr", value="value")
    created = await repository.create(schema)
    repository.update_attr(created.id, "value", "new_value")
    updated = repository.read_by_id(created.id)
    assert updated.value == "new_value"


@pytest.mark.asyncio
async def test_whole_update(repository):
    schema = ModelSchema(name="test_whole", value="value")
    created = await repository.create(schema)
    update_schema = ModelSchema(name="updated_name", value="updated_value")
    updated = repository.whole_update(created.id, update_schema)
    assert updated.name == "updated_name"
    assert updated.value == "updated_value"


def test_read_by_options_with_page_size_all_and_eager(monkeypatch):
    repository, mock_session = build_mocked_repository()
    monkeypatch.setattr(
        "app.repository.base_repository.joinedload", lambda relation: relation
    )
    monkeypatch.setattr(
        "app.repository.base_repository.dict_to_sqlalchemy_filter_options",
        lambda model, schema: True,
    )
    monkeypatch.setattr(Model, "eagers", ["name"], raising=False)

    schema = DummySchema({"ordering": "name", "page": 1, "page_size": "all"})
    base_query = MagicMock()
    filtered_query = MagicMock()
    ordered_query = MagicMock()
    mock_session.query.return_value = base_query
    base_query.options.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.order_by.return_value = ordered_query
    ordered_query.all.return_value = ["item-a", "item-b"]
    filtered_query.count.return_value = 2

    result = repository.read_by_options(schema, eager=True)

    assert result["items"] == ["item-a", "item-b"]
    assert result["search_options"]["page_size"] == "all"
    assert result["search_options"]["total_count"] == 2
    assert base_query.options.called


def test_read_by_options_with_pagination(monkeypatch):
    repository, mock_session = build_mocked_repository()
    monkeypatch.setattr(
        "app.repository.base_repository.dict_to_sqlalchemy_filter_options",
        lambda model, schema: True,
    )

    schema = DummySchema({"ordering": "-name", "page": 2, "page_size": 3})
    base_query = MagicMock()
    filtered_query = MagicMock()
    ordered_query = MagicMock()
    limited_query = MagicMock()
    offset_query = MagicMock()
    mock_session.query.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.order_by.return_value = ordered_query
    ordered_query.limit.return_value = limited_query
    limited_query.offset.return_value = offset_query
    offset_query.all.return_value = ["item-paged"]
    filtered_query.count.return_value = 11

    result = repository.read_by_options(schema)

    assert result["items"] == ["item-paged"]
    assert result["search_options"]["page"] == 2
    assert result["search_options"]["page_size"] == 3
    ordered_query.limit.assert_called_once_with(3)
    limited_query.offset.assert_called_once_with(3)


def test_read_by_id_with_eager_and_not_found_returns_none(monkeypatch):
    repository, mock_session = build_mocked_repository()
    monkeypatch.setattr(
        "app.repository.base_repository.joinedload", lambda relation: relation
    )
    monkeypatch.setattr(Model, "eagers", ["name"], raising=False)

    base_query = MagicMock()
    filtered_query = MagicMock()
    mock_session.query.return_value = base_query
    base_query.options.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.first.return_value = None

    result = repository.read_by_id(999, eager=True, not_found_raise_exception=False)

    assert result is None
    assert base_query.options.called


def test_read_by_column_with_eager_raises_not_found(monkeypatch):
    repository, mock_session = build_mocked_repository()
    monkeypatch.setattr(
        "app.repository.base_repository.joinedload", lambda relation: relation
    )
    monkeypatch.setattr(Model, "eagers", ["name"], raising=False)

    base_query = MagicMock()
    filtered_query = MagicMock()
    mock_session.query.return_value = base_query
    base_query.options.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.first.return_value = None

    with pytest.raises(NotFoundError):
        repository.read_by_column("name", "missing", eager=True)


def test_read_by_column_returns_list_when_only_one_false():
    repository, mock_session = build_mocked_repository()

    base_query = MagicMock()
    filtered_query = MagicMock()
    mock_session.query.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.all.return_value = ["row-1", "row-2"]

    result = repository.read_by_column(
        "name", "value", only_one=False, not_found_raise_exception=False
    )

    assert result == ["row-1", "row-2"]


def test_delete_by_id_raises_not_found_for_missing_record():
    repository, mock_session = build_mocked_repository()

    base_query = MagicMock()
    filtered_query = MagicMock()
    mock_session.query.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.first.return_value = None

    with pytest.raises(NotFoundError):
        repository.delete_by_id(404)


def test_read_by_columns_returns_first_with_eager(monkeypatch):
    repository, mock_session = build_mocked_repository()
    monkeypatch.setattr(
        "app.repository.base_repository.joinedload", lambda relation: relation
    )
    monkeypatch.setattr(Model, "eagers", ["name"], raising=False)

    base_query = MagicMock()
    filtered_query = MagicMock()
    expected = SimpleNamespace(id=1, name="first")
    mock_session.query.return_value = base_query
    base_query.options.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.first.return_value = expected

    result = repository.read_by_columns({"name": "first"}, eager=True, only_one=True)

    assert result == expected


def test_read_by_columns_raises_not_found_when_missing():
    repository, mock_session = build_mocked_repository()

    base_query = MagicMock()
    filtered_query = MagicMock()
    mock_session.query.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.first.return_value = None

    with pytest.raises(NotFoundError):
        repository.read_by_columns({"name": "missing"})


def test_read_by_columns_returns_all_when_only_one_false():
    repository, mock_session = build_mocked_repository()

    base_query = MagicMock()
    filtered_query = MagicMock()
    expected = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    mock_session.query.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.all.return_value = expected

    result = repository.read_by_columns({"name": "any"}, only_one=False)

    assert result == expected
