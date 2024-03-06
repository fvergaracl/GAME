from app.repository.user_points_repository import UserPointsRepository


def get_user_measurements_count(
        user_id: int,
        user_points_repository: UserPointsRepository) -> int:
    """
    Get the number of measurements a user has completed in a campaign.

    Args:
        user_id (int): The user's unique identifier.
        user_points_repository (UserPointsRepository): The repository to access user points data.

    Returns:
        int: The number of measurements completed by the user.
    """
    # Asumiendo que UserPointsRepository tiene un método para contar mediciones por user_id
    measurements_count = user_points_repository.count_measurements_by_user_id(
        user_id)

    return measurements_count
