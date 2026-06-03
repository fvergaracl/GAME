"""
Integration tests for ``BaseRepository``. The repository is exercised
against a real in-memory aiosqlite engine via the shared ``session_factory``
fixture (see ``conftest.py``). This replaces the legacy mocked tests that
targeted the sync ``session.query()`` API which no longer exists.
"""

from contextlib import asynccontextmanager
from typing import Optional

import pytest
import pytest_asyncio
from pydantic import BaseModel as PydBaseModel
from pydantic import ConfigDict
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.exceptions import DuplicatedError, NotFoundError
from app.repository.base_repository import BaseRepository

_Base = declarative_base()


class _BaseRepoModel(_Base):
    """
    Standalone declarative model used only by ``BaseRepository`` tests. It is
    intentionally not part of ``SQLModel.metadata`` so it stays isolated from
    the application schema.
    """

    __tablename__ = "test_base_repo_model"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=True)


class _Schema(PydBaseModel):
    name: str
    value: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class _OrderingSchema(PydBaseModel):
    """Mimics the read_by_options input contract."""

    page: int = 1
    page_size: object = 50
    ordering: str = "id"

    model_config = ConfigDict(from_attributes=True)


@pytest_asyncio.fixture
async def base_repo_session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(_Base.metadata.create_all)
    sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)

    @asynccontextmanager
    async def _factory():
        session = sessionmaker()
        try:
            yield session
        finally:
            await session.close()

    try:
        yield _factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def base_repo(base_repo_session_factory):
    return BaseRepository(base_repo_session_factory, _BaseRepoModel)


@pytest.mark.asyncio
async def test_create_persists_entity_and_returns_it(base_repo):
    created = await base_repo.create(_Schema(name="alpha", value="v"))

    assert created.id is not None
    assert created.name == "alpha"
    assert created.value == "v"


@pytest.mark.asyncio
async def test_create_raises_duplicated_error_on_unique_violation(base_repo):
    await base_repo.create(_Schema(name="dup", value="a"))

    with pytest.raises(DuplicatedError):
        await base_repo.create(_Schema(name="dup", value="b"))


@pytest.mark.asyncio
async def test_create_without_external_session_rejects_auto_commit_false(base_repo):
    with pytest.raises(ValueError):
        await base_repo.create(_Schema(name="x"), auto_commit=False)


@pytest.mark.asyncio
async def test_create_with_external_session_and_auto_commit_false_flushes_only(
    base_repo, base_repo_session_factory
):
    async with base_repo_session_factory() as session:
        created = await base_repo.create(
            _Schema(name="external-tx", value="v"),
            session=session,
            auto_commit=False,
        )
        # No commit yet — visible inside the same transaction only.
        assert created.id is not None
        await session.rollback()

    # After rollback the row must not be there.
    with pytest.raises(NotFoundError):
        await base_repo.read_by_column("name", "external-tx")


@pytest.mark.asyncio
async def test_read_by_id_returns_existing_entity(base_repo):
    created = await base_repo.create(_Schema(name="findme"))

    found = await base_repo.read_by_id(created.id)
    assert found.id == created.id
    assert found.name == "findme"


@pytest.mark.asyncio
async def test_read_by_id_raises_not_found_when_missing(base_repo):
    with pytest.raises(NotFoundError):
        await base_repo.read_by_id(999_999)


@pytest.mark.asyncio
async def test_read_by_id_returns_none_when_not_found_raise_false(base_repo):
    result = await base_repo.read_by_id(999_999, not_found_raise_exception=False)
    assert result is None


@pytest.mark.asyncio
async def test_read_by_column_returns_first_match(base_repo):
    await base_repo.create(_Schema(name="col-a", value="1"))
    await base_repo.create(_Schema(name="col-b", value="2"))

    result = await base_repo.read_by_column("name", "col-a")
    assert result.name == "col-a"


@pytest.mark.asyncio
async def test_read_by_column_raises_not_found_when_missing(base_repo):
    with pytest.raises(NotFoundError):
        await base_repo.read_by_column("name", "absent")


@pytest.mark.asyncio
async def test_read_by_column_returns_list_when_only_one_false(base_repo):
    await base_repo.create(_Schema(name="multi-1", value="shared"))
    await base_repo.create(_Schema(name="multi-2", value="shared"))

    result = await base_repo.read_by_column("value", "shared", only_one=False)
    assert {r.name for r in result} == {"multi-1", "multi-2"}


@pytest.mark.asyncio
async def test_read_by_columns_returns_first_match(base_repo):
    await base_repo.create(_Schema(name="combo", value="green"))

    result = await base_repo.read_by_columns({"name": "combo", "value": "green"})
    assert result.name == "combo"


@pytest.mark.asyncio
async def test_read_by_columns_raises_not_found_when_missing(base_repo):
    with pytest.raises(NotFoundError):
        await base_repo.read_by_columns({"name": "ghost"})


@pytest.mark.asyncio
async def test_read_by_columns_returns_all_when_only_one_false(base_repo):
    await base_repo.create(_Schema(name="m-1", value="x"))
    await base_repo.create(_Schema(name="m-2", value="x"))

    result = await base_repo.read_by_columns({"value": "x"}, only_one=False)
    assert {r.name for r in result} == {"m-1", "m-2"}


@pytest.mark.asyncio
async def test_update_changes_columns(base_repo):
    created = await base_repo.create(_Schema(name="upd", value="old"))

    updated = await base_repo.update(created.id, _Schema(name="upd", value="new"))
    assert updated.value == "new"


@pytest.mark.asyncio
async def test_update_attr_changes_single_column(base_repo):
    created = await base_repo.create(_Schema(name="attr", value="old"))

    updated = await base_repo.update_attr(created.id, "value", "new")
    assert updated.value == "new"


@pytest.mark.asyncio
async def test_whole_update_replaces_all_columns(base_repo):
    created = await base_repo.create(_Schema(name="whole", value="old"))

    updated = await base_repo.whole_update(
        created.id, _Schema(name="whole-new", value="new-v")
    )
    assert updated.name == "whole-new"
    assert updated.value == "new-v"


@pytest.mark.asyncio
async def test_delete_by_id_removes_entity(base_repo):
    created = await base_repo.create(_Schema(name="del"))

    await base_repo.delete_by_id(created.id)

    with pytest.raises(NotFoundError):
        await base_repo.read_by_id(created.id)


@pytest.mark.asyncio
async def test_delete_by_id_raises_not_found_for_missing_record(base_repo):
    with pytest.raises(NotFoundError):
        await base_repo.delete_by_id(999_999)


@pytest.mark.asyncio
async def test_read_by_options_paginates_and_orders(base_repo):
    for i in range(5):
        await base_repo.create(_Schema(name=f"page-{i}"))

    result = await base_repo.read_by_options(
        _OrderingSchema(page=1, page_size=2, ordering="name")
    )
    assert len(result["items"]) == 2
    assert result["search_options"]["total_count"] == 5
    assert [item.name for item in result["items"]] == ["page-0", "page-1"]


@pytest.mark.asyncio
async def test_read_by_options_returns_all_when_page_size_all(base_repo):
    for i in range(3):
        await base_repo.create(_Schema(name=f"all-{i}"))

    result = await base_repo.read_by_options(
        _OrderingSchema(page=1, page_size="all", ordering="-name")
    )
    assert len(result["items"]) == 3
    # Descending ordering by name
    assert [item.name for item in result["items"]] == ["all-2", "all-1", "all-0"]
