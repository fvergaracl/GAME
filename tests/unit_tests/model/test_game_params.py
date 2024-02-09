import pytest
from uuid import uuid4
from app.model.game_params import GamesParams


def test_games_params_creation_and_representation():
    # Prepare data for creating a GamesParams instance
    param_key = "difficulty"
    value = "hard"
    game_id = str(uuid4())  # Assuming UUID is used for game IDs

    # Create a GamesParams instance
    game_params = GamesParams(
        paramKey=param_key,
        value=value,
        gameId=game_id
    )

    # Test the string representation
    expected_str = (
        f"GameParams: (id={game_params.id}, created_at={game_params.created_at}, updated_at={game_params.updated_at}, "
        f"paramKey={param_key}, value={value}, gameId={game_id})"
    )
    assert str(game_params) == expected_str
    assert repr(game_params) == expected_str


def test_games_params_equality():
    game_id = uuid4()
    game_params1 = GamesParams(
        paramKey="difficulty",
        value="hard",
        gameId=game_id
    )
    game_params2 = GamesParams(
        paramKey="difficulty",
        value="hard",
        gameId=game_id
    )
    game_params3 = GamesParams(
        paramKey="level",
        value="10",
        gameId=game_id
    )

    # Test equality
    assert game_params1 == game_params2
    assert game_params1 != game_params3


def test_games_params_hash():
    game_id = uuid4()
    game_params1 = GamesParams(
        paramKey="difficulty",
        value="hard",
        gameId=game_id
    )
    game_params2 = GamesParams(
        paramKey="difficulty",
        value="hard",
        gameId=game_id
    )
    game_params3 = GamesParams(
        paramKey="level",
        value="10",
        gameId=game_id
    )

    # Hashes should be the same for objects with the same content
    assert hash(game_params1) == hash(game_params2)
    # Hashes should differ for objects with different content
    assert hash(game_params1) != hash(game_params3)


if __name__ == "__main__":
    pytest.main()
