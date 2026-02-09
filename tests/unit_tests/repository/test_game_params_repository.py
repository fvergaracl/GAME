from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.repository.game_params_repository import GameParamsRepository


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
    repository = GameParamsRepository(session_factory=session_factory)
    return repository, session


def test_patch_game_params_by_id_updates_fields_and_returns_refreshed_entity():
    repository, session = build_repository()
    query = MagicMock()
    session.query.return_value = query
    query.filter.return_value = query
    game_param = SimpleNamespace(id="param-1", key="difficulty", value="normal")
    query.first.return_value = game_param

    refreshed = SimpleNamespace(id="param-1", key="difficulty", value="hard")
    repository.read_by_id = MagicMock(return_value=refreshed)
    schema = DummySchema({"value": "hard"})

    result = repository.patch_game_params_by_id("param-1", schema)

    assert game_param.value == "hard"
    session.commit.assert_called_once()
    repository.read_by_id.assert_called_once_with(
        "param-1",
        not_found_message="GameParams not found (id) : param-1",
    )
    assert result == refreshed


def test_patch_game_params_by_id_raises_not_found_when_id_does_not_exist():
    repository, session = build_repository()
    query = MagicMock()
    session.query.return_value = query
    query.filter.return_value = query
    query.first.return_value = None
    schema = DummySchema({"value": "hard"})

    with pytest.raises(NotFoundError) as exc_info:
        repository.patch_game_params_by_id("missing-id", schema)

    session.commit.assert_not_called()
    assert exc_info.value.detail == "GameParams not found (id) : missing-id"
