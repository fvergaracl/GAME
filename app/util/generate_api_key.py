import random
import string


def generate_api_key(length=40):
    """
    Generate a random API Key, with a default length of 40 characters.

    Args:
        length (int): Length of the API Key. Defaults to 40.

    Returns:
        str: API Key generated randomly.
    """
    characters = string.ascii_letters + \
        string.digits
    api_key = ''.join(random.choice(characters) for _ in range(length))
    return api_key
