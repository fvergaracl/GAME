from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import DuplicatedError, NotFoundError
from app.repository.game_repository import GameRepository


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
    repository = GameRepository(session_factory=session_factory)
    return repository, session


def build_query(first_result=None, all_result=None, delete_result=1):
    query = MagicMock()
    query.options.return_value = query
    query.filter.return_value = query
    query.order_by.return_value = query
    query.outerjoin.return_value = query
    query.limit.return_value = query
    query.offset.return_value = query
    query.first.return_value = first_result
    query.all.return_value = [] if all_result is None else all_result
    query.delete.return_value = delete_result
    return query


def test_get_all_games_with_eager_api_key_and_page_size_all(monkeypatch):
    repository, session = build_repository()
    monkeypatch.setattr(
        "app.repository.game_repository.dict_to_sqlalchemy_filter_options",
        lambda model, schema: True,
    )
    monkeypatch.setattr("app.repository.game_repository.joinedload", lambda relation: relation)
    monkeypatch.setattr(repository.model, "eagers", ["params"], raising=False)

    base_query = build_query()
    filtered_query = build_query()
    ordered_query = build_query()
    joined_query = build_query()
    api_key_query = build_query()

    session.query.return_value = base_query
    base_query.options.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.order_by.return_value = ordered_query
    ordered_query.outerjoin.return_value = joined_query
    joined_query.filter.return_value = api_key_query

    game_id_1 = uuid4()
    game_id_2 = uuid4()
    now = datetime(2026, 2, 9, 12, 0, 0)
    param = SimpleNamespace(id=uuid4(), key="difficulty", value="hard")
    api_key_query.all.return_value = [
        SimpleNamespace(
            id=game_id_1,
            updated_at=now,
            strategyId="default",
            created_at=now,
            platform="web",
            externalGameId="ext-1",
            GamesParams=param,
        ),
        SimpleNamespace(
            id=game_id_1,
            updated_at=now,
            strategyId="default",
            created_at=now,
            platform="web",
            externalGameId="ext-1",
            GamesParams=None,
        ),
        SimpleNamespace(
            id=game_id_2,
            updated_at=now,
            strategyId="default",
            created_at=now,
            platform="mobile",
            externalGameId="ext-2",
            GamesParams=None,
        ),
    ]

    schema = DummySchema(
        {
            "ordering": "-id",
            "page": 1,
            "page_size": "all",
            "eager": True,
            "externalGameId": "ext-1",
        }
    )
    result = repository.get_all_games(schema, api_key="api-key-1")

    assert result.search_options.page == 1
    assert result.search_options.page_size == "all"
    assert result.search_options.ordering == "-id"
    assert result.search_options.total_count == 2
    assert len(result.items) == 2

    items_by_id = {item.gameId: item for item in result.items}
    assert len(items_by_id[game_id_1].params) == 1
    assert items_by_id[game_id_1].params[0]["id"] == param.id
    assert items_by_id[game_id_1].params[0]["key"] == "difficulty"
    assert items_by_id[game_id_1].params[0]["value"] == "hard"
    assert items_by_id[game_id_2].params == []
    assert base_query.options.called
    joined_query.filter.assert_called_once()


def test_get_all_games_with_pagination(monkeypatch):
    repository, session = build_repository()
    monkeypatch.setattr(
        "app.repository.game_repository.dict_to_sqlalchemy_filter_options",
        lambda model, schema: True,
    )

    base_query = build_query()
    filtered_query = build_query()
    ordered_query = build_query()
    joined_query = build_query()
    limited_query = build_query()
    offset_query = build_query()

    session.query.return_value = base_query
    base_query.filter.return_value = filtered_query
    filtered_query.order_by.return_value = ordered_query
    ordered_query.outerjoin.return_value = joined_query
    joined_query.limit.return_value = limited_query
    limited_query.offset.return_value = offset_query

    game_id = uuid4()
    now = datetime(2026, 2, 9, 12, 0, 0)
    offset_query.all.return_value = [
        SimpleNamespace(
            id=game_id,
            updated_at=now,
            strategyId="default",
            created_at=now,
            platform="web",
            externalGameId="ext-1",
            GamesParams=None,
        )
    ]

    schema = DummySchema({"ordering": "id", "page": 2, "page_size": 3})
    result = repository.get_all_games(schema)

    assert result.search_options.page == 2
    assert result.search_options.page_size == 3
    assert result.search_options.ordering == "id"
    assert result.search_options.total_count == 1
    assert len(result.items) == 1
    joined_query.limit.assert_called_once_with(3)
    limited_query.offset.assert_called_once_with(3)


def test_get_game_by_id_success():
    repository, session = build_repository()

    game_id = uuid4()
    now = datetime(2026, 2, 9, 12, 0, 0)
    game = SimpleNamespace(
        id=game_id,
        created_at=now,
        updated_at=now,
        externalGameId="ext-1",
        platform="web",
    )
    params = [
        SimpleNamespace(id=uuid4(), key="difficulty", value="hard"),
        SimpleNamespace(id=uuid4(), key="lives", value="3"),
    ]

    game_query = build_query(first_result=game)
    params_query = build_query(all_result=params)
    session.query.side_effect = [game_query, params_query]

    result = repository.get_game_by_id(game_id)

    assert result.gameId == game_id
    assert result.externalGameId == "ext-1"
    assert result.platform == "web"
    assert len(result.params) == 2
    assert result.params[0].key == "difficulty"
    assert result.params[0].value == "hard"


def test_get_game_by_id_raises_not_found_for_missing_game():
    repository, session = build_repository()

    game_query = build_query(first_result=None)
    session.query.return_value = game_query

    with pytest.raises(NotFoundError):
        repository.get_game_by_id(uuid4())


def test_patch_game_by_id_success(monkeypatch):
    repository, session = build_repository()

    game_id = uuid4()
    game = SimpleNamespace(
        id=game_id,
        externalGameId="old-external",
        platform="web",
        strategyId="old-strategy",
    )
    game_query = build_query(first_result=game)
    session.query.return_value = game_query

    expected = SimpleNamespace(gameId=game_id)
    get_game_by_id_mock = MagicMock(return_value=expected)
    monkeypatch.setattr(repository, "get_game_by_id", get_game_by_id_mock)

    schema = DummySchema(
        {
            "externalGameId": "new-external",
            "platform": "mobile",
            "strategyId": "new-strategy",
            "params": None,
        }
    )
    result = repository.patch_game_by_id(game_id, schema)

    assert game.externalGameId == "new-external"
    assert game.platform == "mobile"
    assert game.strategyId == "new-strategy"
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(game)
    get_game_by_id_mock.assert_called_once_with(game_id)
    assert result == expected


def test_patch_game_by_id_raises_not_found_for_missing_game():
    repository, session = build_repository()

    game_query = build_query(first_result=None)
    session.query.return_value = game_query

    with pytest.raises(NotFoundError):
        repository.patch_game_by_id(uuid4(), DummySchema({"platform": "mobile"}))


def test_patch_game_by_id_raises_duplicated_error_on_integrity_error():
    repository, session = build_repository()

    game_id = uuid4()
    game_query = build_query(first_result=SimpleNamespace(id=game_id, platform="web"))
    session.query.return_value = game_query
    session.commit.side_effect = IntegrityError("stmt", {}, Exception("duplicated game"))

    with pytest.raises(DuplicatedError) as exc_info:
        repository.patch_game_by_id(game_id, DummySchema({"platform": "mobile"}))

    assert "duplicated game" in str(exc_info.value.detail)


def test_delete_game_by_id_success():
    repository, session = build_repository()

    game_id = uuid4()
    game = SimpleNamespace(id=game_id)
    task_1 = SimpleNamespace(id=uuid4())
    task_2 = SimpleNamespace(id=uuid4())

    game_query = build_query(first_result=game)
    game_params_query = build_query()
    tasks_query = build_query(all_result=[task_1, task_2])
    task_1_params_query = build_query()
    task_1_user_points_query = build_query()
    task_2_params_query = build_query()
    task_2_user_points_query = build_query()
    tasks_delete_query = build_query()

    session.query.side_effect = [
        game_query,
        game_params_query,
        tasks_query,
        task_1_params_query,
        task_1_user_points_query,
        task_2_params_query,
        task_2_user_points_query,
        tasks_delete_query,
    ]

    result = repository.delete_game_by_id(game_id)

    assert result is True
    assert game_params_query.delete.call_count == 1
    assert task_1_params_query.delete.call_count == 1
    assert task_1_user_points_query.delete.call_count == 1
    assert task_2_params_query.delete.call_count == 1
    assert task_2_user_points_query.delete.call_count == 1
    assert tasks_delete_query.delete.call_count == 1
    session.delete.assert_called_once_with(game)
    session.commit.assert_called_once()


def test_delete_game_by_id_raises_not_found_when_game_missing():
    repository, session = build_repository()

    game_query = build_query(first_result=None)
    session.query.return_value = game_query
    game_id = uuid4()

    with pytest.raises(NotFoundError) as exc_info:
        repository.delete_game_by_id(game_id)

    assert "Not found id" in str(exc_info.value.detail)


def test_delete_game_by_id_raises_duplicated_error_on_integrity_error():
    repository, session = build_repository()

    game_id = uuid4()
    game = SimpleNamespace(id=game_id)
    task = SimpleNamespace(id=uuid4())

    game_query = build_query(first_result=game)
    game_params_query = build_query()
    tasks_query = build_query(all_result=[task])
    task_params_query = build_query()
    user_points_query = build_query()
    tasks_delete_query = build_query()

    session.query.side_effect = [
        game_query,
        game_params_query,
        tasks_query,
        task_params_query,
        user_points_query,
        tasks_delete_query,
    ]
    session.commit.side_effect = IntegrityError("stmt", {}, Exception("delete duplicated"))

    with pytest.raises(DuplicatedError) as exc_info:
        repository.delete_game_by_id(game_id)

    assert "delete duplicated" in str(exc_info.value.detail)


def test_delete_game_by_id_raises_not_found_for_unexpected_errors():
    repository, session = build_repository()

    game_id = uuid4()
    game = SimpleNamespace(id=game_id)
    task = SimpleNamespace(id=uuid4())

    game_query = build_query(first_result=game)
    game_params_query = build_query()
    tasks_query = build_query(all_result=[task])
    task_params_query = build_query()
    user_points_query = build_query()
    tasks_delete_query = build_query()

    session.query.side_effect = [
        game_query,
        game_params_query,
        tasks_query,
        task_params_query,
        user_points_query,
        tasks_delete_query,
    ]
    session.commit.side_effect = RuntimeError("commit exploded")

    with pytest.raises(NotFoundError) as exc_info:
        repository.delete_game_by_id(game_id)

    assert "commit exploded" in str(exc_info.value.detail)
