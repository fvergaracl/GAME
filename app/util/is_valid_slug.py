import re


def is_valid_slug(slug, min_length=3, max_length=60):
    """
    Validates a slug.
    :param slug: The slug to validate.
    :type slug: str
    :return: True if the slug is valid, False otherwise.
    :rtype: bool


    """
    return re.match(
        r"^[a-zA-Z0-9_]{" + str(min_length) + "," + str(max_length) + "}$",
        slug) is not None
