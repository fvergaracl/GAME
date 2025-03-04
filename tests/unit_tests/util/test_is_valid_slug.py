import unittest

from app.util.is_valid_slug import is_valid_slug, is_valid_slug_or_email


class TestIsValidSlug(unittest.TestCase):

    def test_valid_slug(self):
        """
        Test that valid slugs pass the validation.
        """
        self.assertTrue(is_valid_slug("valid-slug_123"))
        self.assertTrue(is_valid_slug("another_valid-slug"))
        self.assertTrue(is_valid_slug("slug_with_numbers_987"))

    def test_invalid_slug_special_characters(self):
        """
        Test that slugs with invalid special characters fail the validation.
        """
        self.assertFalse(is_valid_slug("invalid_slug!"))
        self.assertFalse(is_valid_slug("invalid@slug"))
        self.assertFalse(is_valid_slug("slug#with$special%chars"))

    def test_invalid_slug_whitespace(self):
        """
        Test that slugs with whitespace fail the validation.
        """
        self.assertFalse(is_valid_slug("invalid slug"))
        self.assertFalse(is_valid_slug("slug with space"))
        self.assertFalse(is_valid_slug(" slug_with_leading_space"))
        self.assertFalse(is_valid_slug("slug_with_trailing_space "))

    def test_invalid_slug_too_short(self):
        """
        Test that slugs shorter than the minimum length fail the validation.
        """
        self.assertFalse(is_valid_slug("a"))
        self.assertFalse(is_valid_slug("ab"))

    def test_invalid_slug_too_long(self):
        """
        Test that slugs longer than the maximum length fail the validation.
        """
        long_slug = "a" * 61
        self.assertFalse(is_valid_slug(long_slug))

    def test_valid_slug_custom_length(self):
        """
        Test slugs with custom min and max length.
        """
        self.assertTrue(is_valid_slug("short", min_length=3, max_length=10))
        self.assertFalse(is_valid_slug("too_long_for_custom_max", max_length=10))

        self.assertFalse(is_valid_slug("xy", min_length=3))

    def test_invalid_empty_slug(self):
        """
        Test that an empty string is an invalid slug.
        """
        self.assertFalse(is_valid_slug(""))

    # def is_valid_slug_or_email(value, min_length=3, max_length=60):
    # """
    # Validates a slug or an email address.
    # :param value: The slug or email to validate.
    # :type value: str
    # :param min_length: Minimum length of the slug.
    # :type min_length: int
    # :param max_length: Maximum length of the slug.
    # :type max_length: int
    # :return: True if the value is a valid slug or email, False otherwise.
    # :rtype: bool
    # """
    # slug_pattern = rf"^[a-z0-9_-]{{{min_length},{max_length}}}$"
    # email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    # if re.fullmatch(slug_pattern, value, re.IGNORECASE):
    #     return True
    # elif re.fullmatch(email_pattern, value):
    #     return True
    # else:
    #     return False

    def test_valid_slug_or_email(self):
        """
        Test that valid slugs and email addresses pass the validation.
        """
        self.assertTrue(is_valid_slug_or_email("valid-slug_123"))
        self.assertTrue(is_valid_slug_or_email("another_valid-slug"))
        self.assertTrue(is_valid_slug_or_email("slug_with_numbers_987"))
        self.assertTrue(is_valid_slug_or_email("example@example.com"))
        self.assertTrue(is_valid_slug_or_email("example+example@example.com"))

    def test_invalid_slug_or_email_special_characters(self):
        """
        Test that slugs with invalid special characters fail the validation.
        """
        self.assertFalse(is_valid_slug_or_email("invalid_slug!"))
        self.assertFalse(is_valid_slug_or_email("invalid@slug"))
        self.assertFalse(is_valid_slug_or_email("slug#with$special%chars"))
        self.assertFalse(is_valid_slug_or_email("example@example!com"))
        self.assertFalse(is_valid_slug_or_email("example@example#com"))
        self.assertFalse(is_valid_slug_or_email("example example com"))


if __name__ == "__main__":
    unittest.main()
