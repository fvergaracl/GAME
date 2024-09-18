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


def is_valid_slug_or_email(value, min_length=3, max_length=60):
    """
    Validates a slug or an email address.
    :param value: The slug or email to validate.
    :type value: str
    :param min_length: Minimum length of the slug.
    :type min_length: int
    :param max_length: Maximum length of the slug.
    :type max_length: int
    :return: True if the value is a valid slug or email, False otherwise.
    :rtype: bool
    """
    slug_pattern = rf"^[a-z0-9_-]{{{min_length},{max_length}}}$"
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if re.fullmatch(slug_pattern, value, re.IGNORECASE):
        return True
    elif re.fullmatch(email_pattern, value):
        return True
    else:
        return False
