import re


def is_valid_slug(slug, min_length=3, max_length=60):
    """
    Validates a slug.
    :param slug: The slug to validate.
    :type slug: str
    :param min_length: Minimum length of the slug.
    :type min_length: int
    :param max_length: Maximum length of the slug.
    :type max_length: int
    :return: True if the slug is valid, False otherwise.
    :rtype: bool
    """
    pattern = rf"^[a-z0-9_-]{{{min_length},{max_length}}}$"
    return re.fullmatch(pattern, slug, re.IGNORECASE) is not None
