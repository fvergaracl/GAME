from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.repository.task_repository import TaskRepository


class DummySchema:
    def __init__(self, payload):
        self.payload = payload

    def dict(self, exclude_none=False):
        if exclude_none:
            return {k: v for k, v in self.payload.items() if v is not None}
        return dict(self.payload)


def build_repository():
    session = MagicMock()
    context_manager = MagicMock()
    context_manager.__enter__.return_value = session
    context_manager.__exit__.return_value = False
    session_factory = MagicMock(return_value=context_manager)
    repository = TaskRepository(session_factory=session_factory)
    return repository, session


def test_read_by_game_id_with_eager_and_page_size_all(monkeypatch):
    repository, session = build_repository()
    monkeypatch.setattr(
        "app.repository.task_repository.dict_to_sqlalchemy_filter_options",
        lambda model, schema: True,
    )
    monkeypatch.setattr(
        "app.repository.task_repository.joinedload", lambda relation: relation
    )
    monkeypatch.setattr(repository.model, "eagers", ["strategyId"], raising=False)

    base_query = MagicMock()
    filtered_query = MagicMock()
    ordered_query = MagicMock()

    session.query.return_value = base_query
    base_query.options.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.order_by.return_value = ordered_query
    ordered_query.all.return_value = ["task-a", "task-b"]
    filtered_query.count.return_value = 2

    schema = DummySchema(
        {
            "gameId": "game-1",
            "ordering": "-id",
            "page": 1,
            "page_size": "all",
        }
    )

    result = repository.read_by_gameId(schema, eager=True)

    assert result["items"] == ["task-a", "task-b"]
    assert result["search_options"]["page"] == 1
    assert result["search_options"]["page_size"] == "all"
    assert result["search_options"]["ordering"] == "-id"
    assert result["search_options"]["total_count"] == 2
    assert base_query.options.called


def test_read_by_game_id_with_pagination(monkeypatch):
    repository, session = build_repository()
    monkeypatch.setattr(
        "app.repository.task_repository.dict_to_sqlalchemy_filter_options",
        lambda model, schema: True,
    )

    base_query = MagicMock()
    filtered_query = MagicMock()
    ordered_query = MagicMock()
    limited_query = MagicMock()
    offset_query = MagicMock()

    session.query.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.order_by.return_value = ordered_query
    ordered_query.limit.return_value = limited_query
    limited_query.offset.return_value = offset_query
    offset_query.all.return_value = ["task-paged"]
    filtered_query.count.return_value = 11

    schema = DummySchema(
        {
            "gameId": "game-1",
            "ordering": "id",
            "page": 2,
            "page_size": 3,
        }
    )

    result = repository.read_by_gameId(schema)

    assert result["items"] == ["task-paged"]
    assert result["search_options"]["page"] == 2
    assert result["search_options"]["page_size"] == 3
    assert result["search_options"]["ordering"] == "id"
    assert result["search_options"]["total_count"] == 11
    ordered_query.limit.assert_called_once_with(3)
    limited_query.offset.assert_called_once_with(3)


def test_read_by_game_id_and_external_task_id_returns_first_match():
    repository, session = build_repository()
    query = MagicMock()
    session.query.return_value = query
    query.filter.return_value = query
    expected = SimpleNamespace(id="task-1", externalTaskId="task-ext-1")
    query.first.return_value = expected

    result = repository.read_by_gameId_and_externalTaskId("game-1", "task-ext-1")

    assert result == expected
    query.filter.assert_called_once()
    query.first.assert_called_once()


def test_get_points_and_users_by_task_id_returns_task_when_exists():
    repository, session = build_repository()
    query = MagicMock()
    session.query.return_value = query
    query.filter.return_value = query
    expected = SimpleNamespace(id="task-1")
    query.first.return_value = expected

    result = repository.get_points_and_users_by_taskId("task-1")

    assert result == expected
    query.first.assert_called_once()


def test_get_points_and_users_by_task_id_raises_not_found_when_missing():
    repository, session = build_repository()
    query = MagicMock()
    session.query.return_value = query
    query.filter.return_value = query
    query.first.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        repository.get_points_and_users_by_taskId("missing-task")

    assert "Task not found by id : missing-task" == exc_info.value.detail
