import pytest
from datetime import datetime, timezone
from app.model.games import Games


def test_games_instance_creation_and_representation():
    # Prepare data for creating a Games instance
    external_game_id = "game123"
    platform = "PC"
    end_date_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Create a Games instance
    game = Games(
        externalGameId=external_game_id,
        platform=platform,
        endDateTime=end_date_time
    )

    # Test the string representation
    expected_str = (
        f" Games: (id: {game.id}, created_at: {game.created_at}, updated_at: {game.updated_at}, "
        f"externalGameId: {external_game_id}, platform: {platform}, endDateTime: {end_date_time})"
    )
    assert str(game) == expected_str
    assert repr(game) == expected_str


def test_games_equality():
    game1 = Games(
        externalGameId="game123",
        platform="PC",
        endDateTime=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )
    game2 = Games(
        externalGameId="game123",
        platform="PC",
        endDateTime=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )
    game3 = Games(
        externalGameId="game124",
        platform="Console",
        endDateTime=datetime(2024, 1, 2, 13, 0, 0, tzinfo=timezone.utc)
    )

    # Test equality
    assert game1 == game2
    assert game1 != game3


def test_games_hash():
    game1 = Games(
        externalGameId="game123",
        platform="PC",
        endDateTime=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )
    game2 = Games(
        externalGameId="game123",
        platform="PC",
        endDateTime=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )
    game3 = Games(
        externalGameId="game124",
        platform="Console",
        endDateTime=datetime(2024, 1, 2, 13, 0, 0, tzinfo=timezone.utc)
    )

    # Hashes should be the same for objects with the same content
    assert hash(game1) == hash(game2)
    # Hashes should differ for objects with different content
    assert hash(game1) != hash(game3)


if __name__ == "__main__":
    pytest.main()
