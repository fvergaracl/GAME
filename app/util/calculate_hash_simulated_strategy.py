import hashlib
import json

from app.core.config import configs


def calculate_hash_simulated_strategy(tasks_simulated, game_id, external_user_id):
    """
    Calculate the hash for the simulated strategy.

    Args:
        tasks_simulated (List[dict]): The simulated tasks.
        game_id (str): The game ID.
        external_user_id (str): The external user ID.

    Returns:
        str: The hash of the simulated strategy.
    """
    tasks_str = str(tasks_simulated)
    raw_string = tasks_str + configs.SECRET_KEY + \
        str(game_id) + external_user_id

    new_hash = hashlib.sha256(raw_string.encode()).hexdigest()

    return new_hash
