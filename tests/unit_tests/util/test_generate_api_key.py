import unittest
from app.util.generate_api_key import generate_api_key
import string


class TestGenerateApiKey(unittest.TestCase):

    def test_default_length(self):
        """
        Test that the API key generated has the default length of 40
          characters.
        """
        api_key = generate_api_key()
        self.assertEqual(len(api_key), 40)

    def test_custom_length(self):
        """
        Test that the API key generated has the custom length specified.
        """
        custom_length = 50
        api_key = generate_api_key(length=custom_length)
        self.assertEqual(len(api_key), custom_length)

    def test_only_alphanumeric_characters(self):
        """
        Test that the API key contains only alphanumeric characters.
        """
        api_key = generate_api_key()
        allowed_characters = string.ascii_letters + string.digits
        for char in api_key:
            self.assertIn(char, allowed_characters)

    def test_zero_length(self):
        """
        Test that the API key generated with a length of 0 is an empty string.
        """
        api_key = generate_api_key(length=0)
        self.assertEqual(api_key, "")

    def test_negative_length(self):
        """
        Test that generating an API key with a negative length returns an
          empty string.
        """
        api_key = generate_api_key(length=-5)
        self.assertEqual(api_key, "")


if __name__ == "__main__":
    unittest.main()
