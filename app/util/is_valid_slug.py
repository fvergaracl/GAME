import re


def is_valid_slug(slug):
    """
    Validates a slug.
    :param slug: The slug to validate.
    :type slug: str
    :return: True if the slug is valid, False otherwise.
    :rtype: bool


    """
    return re.match(r"^[a-zA-Z0-9_]{3,60}$", slug) is not None