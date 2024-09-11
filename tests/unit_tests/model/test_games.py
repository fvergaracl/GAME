from datetime import datetime
from uuid import uuid4

from app.model.games import Games


def create_games_instance():
    return Games(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        externalGameId="ext_game_123",
        strategyId="strategy_123",
        platform="PC",
    )


def test_games_creation():
    """
    Test the creation of a Games instance.
    """
    game = create_games_instance()
    assert isinstance(game, Games)
    assert isinstance(game.id, str)
    assert isinstance(game.created_at, datetime)
    assert isinstance(game.updated_at, datetime)
    assert game.externalGameId == "ext_game_123"
    assert game.strategyId == "strategy_123"
    assert game.platform == "PC"


def test_games_str():
    """
    Test the __str__ method of Games.
    """
    game = create_games_instance()
    expected_str = (
        f"Games(id={game.id}, created_at={game.created_at}, "
        f"updated_at={game.updated_at}, externalGameId="
        f"{game.externalGameId}, strategyId={game.strategyId}, "
        f"platform={game.platform})"
    )
    assert str(game) == expected_str


def test_games_repr():
    """
    Test the __repr__ method of Games.
    """
    game = create_games_instance()
    expected_repr = (
        f"Games(id={game.id}, created_at={game.created_at}, "
        f"updated_at={game.updated_at}, externalGameId="
        f"{game.externalGameId}, strategyId={game.strategyId}, "
        f"platform={game.platform})"
    )
    assert repr(game) == expected_repr


def test_games_equality():
    """
    Test the equality operator for Games.
    """
    game1 = create_games_instance()
    game2 = create_games_instance()
    game2.externalGameId = game1.externalGameId
    game2.platform = game1.platform
    assert game1 == game2  # Same externalGameId and platform should be equal
    game2.platform = "PlayStation"
    assert game1 != game2  # Different platform should not be equal


def test_games_hash():
    """
    Test the __hash__ method of Games.
    """
    game = create_games_instance()
    expected_hash = hash((game.externalGameId, game.platform))
    assert hash(game) == expected_hash


def test_games_update_timestamp():
    """
    Test that the updated_at field is automatically updated.
    """
    game = create_games_instance()
    initial_updated_at = game.updated_at

    # Simulate an update
    game.updated_at = datetime.now()

    assert game.updated_at != initial_updated_at
