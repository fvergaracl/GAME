from uuid import uuid4
from app.schema.games_params_schema import (
    BaseGameParams, BaseCreateGameParams, InsertGameParams,
    CreateGameParams, BaseFindGameParams, UpdateGameParams
)


def test_base_game_params():
    """
    Test the BaseGameParams model.

    The BaseGameParams model is used as a base model for game parameters.

    The model has the following attributes:
    - key (str): Parameter key
    - value (str | int | float | bool): Parameter value
    """
    data = {
        "key": "difficulty",
        "value": "hard"
    }
    params = BaseGameParams(**data)
    assert params.key == data["key"]
    assert params.value == data["value"]


def test_base_create_game_params():
    """
    Test the BaseCreateGameParams model.

    The BaseCreateGameParams model is used for creating game parameters.
    """
    data = {
        "key": "difficulty",
        "value": "hard"
    }
    params = BaseCreateGameParams(**data)
    assert params.key == data["key"]
    assert params.value == data["value"]


def test_insert_game_params():
    """
    Test the InsertGameParams model.

    The InsertGameParams model is used for inserting game parameters.

    The model has the following attributes:
    - key (str): Parameter key
    - value (str | int | float | bool): Parameter value
    - gameId (str): Game ID
    """
    data = {
        "key": "difficulty",
        "value": "hard",
        "gameId": "game123"
    }
    params = InsertGameParams(**data)
    assert params.key == data["key"]
    assert params.value == data["value"]
    assert params.gameId == data["gameId"]


def test_create_game_params():
    """
    Test the CreateGameParams model.

    The CreateGameParams model is used for creating game parameters.
    """
    data = {
        "key": "difficulty",
        "value": "hard"
    }
    params = CreateGameParams(**data)
    assert params.key == data["key"]
    assert params.value == data["value"]


def test_base_find_game_params():
    """
    Test the BaseFindGameParams model.

    The BaseFindGameParams model is used for finding game parameters.

    The model has the following attributes:
    - id (UUID): Unique identifier
    - key (str): Parameter key
    - value (str | int | float | bool): Parameter value
    """
    data = {
        "id": uuid4(),
        "key": "difficulty",
        "value": "hard"
    }
    params = BaseFindGameParams(**data)
    assert params.id == data["id"]
    assert params.key == data["key"]
    assert params.value == data["value"]


def test_update_game_params():
    """
    Test the UpdateGameParams model.

    The UpdateGameParams model is used for updating game parameters.

    The model has the following attributes:
    - id (UUID): Unique identifier
    - key (str): Parameter key
    - value (str | int | float | bool): Parameter value
    """
    data = {
        "id": uuid4(),
        "key": "difficulty",
        "value": "hard"
    }
    params = UpdateGameParams(**data)
    assert params.id == data["id"]
    assert params.key == data["key"]
    assert params.value == data["value"]
