from datetime import datetime
from uuid import uuid4

from app.model.game_params import GamesParams


def create_games_params_instance():
    return GamesParams(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        key="test_key",
        value="test_value",
        gameId=str(uuid4()),
    )


def test_games_params_creation():
    """
    Test the creation of a GamesParams instance.
    """
    params = create_games_params_instance()
    assert isinstance(params, GamesParams)
    assert isinstance(params.id, str)
    assert isinstance(params.created_at, datetime)
    assert isinstance(params.updated_at, datetime)
    assert params.key == "test_key"
    assert params.value == "test_value"
    assert isinstance(params.gameId, str)


def test_games_params_str():
    """
    Test the __str__ method of GamesParams.
    """
    params = create_games_params_instance()
    expected_str = (
        f"GameParams: (id={params.id}, created_at={params.created_at}, "
        f"updated_at={params.updated_at}, key={params.key}, "
        f"value={params.value}, gameId={params.gameId})"
    )
    assert str(params) == expected_str


def test_games_params_repr():
    """
    Test the __repr__ method of GamesParams.
    """
    params = create_games_params_instance()
    expected_repr = (
        f"GameParams: (id={params.id}, created_at={params.created_at}, "
        f"updated_at={params.updated_at}, key={params.key}, "
        f"value={params.value}, gameId={params.gameId})"
    )
    assert repr(params) == expected_repr


def test_games_params_equality():
    """
    Test the equality operator for GamesParams.
    """
    params1 = create_games_params_instance()
    params2 = create_games_params_instance()
    assert params1 != params2  # Different instances should not be equal
    assert params1 == params1  # Same instance should be equal to itself


def test_games_params_hash():
    """
    Test the __hash__ method of GamesParams.
    """
    params = create_games_params_instance()
    expected_hash = hash((params.key, params.value, params.gameId))
    assert hash(params) == expected_hash


def test_games_params_update_timestamp():
    """
    Test that the updated_at field is automatically updated.
    """
    params = create_games_params_instance()
    initial_updated_at = params.updated_at

    # Simulate an update
    params.updated_at = datetime.now()

    assert params.updated_at != initial_updated_at
