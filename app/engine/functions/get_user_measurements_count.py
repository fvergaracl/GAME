from app.repository.user_points_repository import UserPointsRepository
from app.repository.task_repository import TaskRepository
from app.repository.game_repository import GameRepository

def get_user_measurements_count_game(
        user_id: int,
        user_points_repository: UserPointsRepository,

        ) -> int:
    """
    Get the number of measurements of a user in the game.

    Args:
    user_id: int
        The user id.
    user_points_repository: UserPointsRepository
        The user points repository.
    Returns:
    int: The number of measurements of the user in the game.
    """

