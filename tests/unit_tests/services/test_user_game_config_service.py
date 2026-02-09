from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.schema.user_game_config_schema import (CreateUserGameConfig,
                                                UpdateUserGameConfig)
from app.services.user_game_config_service import UserGameConfigService


def _build_config(
    user_id="00000000-0000-0000-0000-000000000001",
    game_id="00000000-0000-0000-0000-000000000002",
    experiment_group="group-a",
    config_data=None,
):
    if config_data is None:
        config_data = {"difficulty": "normal"}
    return SimpleNamespace(
        id=uuid4(),
        userId=user_id,
        gameId=game_id,
        experimentGroup=experiment_group,
        configData=config_data,
        created_at=datetime(2026, 2, 9, 0, 0, 0),
        updated_at=datetime(2026, 2, 9, 0, 0, 0),
    )


def test_init_sets_repository():
    repository = MagicMock()
    service = UserGameConfigService(repository)

    assert service.repository is repository


def test_get_user_config_returns_response_when_config_exists():
    repository = MagicMock()
    config = _build_config()
    repository.get_by_user_and_game.return_value = config
    service = UserGameConfigService(repository)

    result = service.get_user_config(config.userId, config.gameId)

    assert result is not None
    assert result.userId == config.userId
    assert result.gameId == config.gameId
    assert result.experimentGroup == config.experimentGroup
    assert result.configData == config.configData
    repository.get_by_user_and_game.assert_called_once_with(
        config.userId, config.gameId
    )


def test_get_user_config_returns_none_when_missing():
    repository = MagicMock()
    repository.get_by_user_and_game.return_value = None
    service = UserGameConfigService(repository)

    result = service.get_user_config("user-id", "game-id")

    assert result is None


def test_create_user_config_calls_repository_and_returns_response():
    repository = MagicMock()
    config = _build_config(
        user_id="00000000-0000-0000-0000-000000000010",
        game_id="00000000-0000-0000-0000-000000000020",
        experiment_group="group-b",
        config_data={"featureX": True},
    )
    repository.create_or_update.return_value = config
    service = UserGameConfigService(repository)
    schema = CreateUserGameConfig(
        userId=config.userId,
        gameId=config.gameId,
        experimentGroup=config.experimentGroup,
        configData=config.configData,
    )

    result = service.create_user_config(schema)

    repository.create_or_update.assert_called_once_with(
        config.userId, config.gameId, config.experimentGroup, config.configData
    )
    assert result.userId == config.userId
    assert result.gameId == config.gameId
    assert result.experimentGroup == config.experimentGroup
    assert result.configData == config.configData


def test_update_user_config_returns_none_when_existing_config_not_found():
    repository = MagicMock()
    repository.get_by_user_and_game.return_value = None
    service = UserGameConfigService(repository)
    schema = UpdateUserGameConfig(experimentGroup="group-c", configData={"k": "v"})

    result = service.update_user_config("user-id", "game-id", schema)

    assert result is None
    repository.create_or_update.assert_not_called()


def test_update_user_config_uses_schema_values_when_provided():
    repository = MagicMock()
    existing = _build_config(experiment_group="group-old", config_data={"old": True})
    updated = _build_config(experiment_group="group-new", config_data={"new": True})
    repository.get_by_user_and_game.return_value = existing
    repository.create_or_update.return_value = updated
    service = UserGameConfigService(repository)
    schema = UpdateUserGameConfig(
        experimentGroup="group-new",
        configData={"new": True},
    )

    result = service.update_user_config(existing.userId, existing.gameId, schema)

    repository.create_or_update.assert_called_once_with(
        existing.userId,
        existing.gameId,
        "group-new",
        {"new": True},
    )
    assert result.experimentGroup == "group-new"
    assert result.configData == {"new": True}


def test_update_user_config_uses_existing_values_when_schema_fields_are_none():
    repository = MagicMock()
    existing = _build_config(experiment_group="group-existing", config_data={"a": 1})
    repository.get_by_user_and_game.return_value = existing
    repository.create_or_update.return_value = existing
    service = UserGameConfigService(repository)
    schema = UpdateUserGameConfig(experimentGroup=None, configData=None)

    result = service.update_user_config(existing.userId, existing.gameId, schema)

    repository.create_or_update.assert_called_once_with(
        existing.userId,
        existing.gameId,
        "group-existing",
        {"a": 1},
    )
    assert result.experimentGroup == "group-existing"
    assert result.configData == {"a": 1}


def test_delete_user_config_delegates_to_repository():
    repository = MagicMock()
    repository.delete.return_value = True
    service = UserGameConfigService(repository)

    result = service.delete_user_config("user-id", "game-id")

    assert result is True
    repository.delete.assert_called_once_with("user-id", "game-id")
