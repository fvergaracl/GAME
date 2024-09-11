import unittest
from app.util.is_valid_slug import is_valid_slug


class TestIsValidSlug(unittest.TestCase):

    def test_valid_slug(self):
        """
        Test that valid slugs pass the validation.
        """
        self.assertTrue(is_valid_slug('valid-slug_123'))
        self.assertTrue(is_valid_slug('another_valid-slug'))
        self.assertTrue(is_valid_slug('slug_with_numbers_987'))

    def test_invalid_slug_special_characters(self):
        """
        Test that slugs with invalid special characters fail the validation.
        """
        self.assertFalse(is_valid_slug('invalid_slug!'))
        self.assertFalse(is_valid_slug('invalid@slug'))
        self.assertFalse(is_valid_slug('slug#with$special%chars'))

    def test_invalid_slug_whitespace(self):
        """
        Test that slugs with whitespace fail the validation.
        """
        self.assertFalse(is_valid_slug('invalid slug'))
        self.assertFalse(is_valid_slug('slug with space'))
        self.assertFalse(is_valid_slug(' slug_with_leading_space'))
        self.assertFalse(is_valid_slug('slug_with_trailing_space '))

    def test_invalid_slug_too_short(self):
        """
        Test that slugs shorter than the minimum length fail the validation.
        """
        self.assertFalse(is_valid_slug('a'))
        self.assertFalse(is_valid_slug('ab'))

    def test_invalid_slug_too_long(self):
        """
        Test that slugs longer than the maximum length fail the validation.
        """
        long_slug = 'a' * 61
        self.assertFalse(is_valid_slug(long_slug))

    def test_valid_slug_custom_length(self):
        """
        Test slugs with custom min and max length.
        """
        self.assertTrue(is_valid_slug('short', min_length=3, max_length=10))
        self.assertFalse(is_valid_slug(
            'too_long_for_custom_max', max_length=10))

        self.assertFalse(is_valid_slug('xy', min_length=3))

    def test_invalid_empty_slug(self):
        """
        Test that an empty string is an invalid slug.
        """
        self.assertFalse(is_valid_slug(''))


if __name__ == "__main__":
    unittest.main()
