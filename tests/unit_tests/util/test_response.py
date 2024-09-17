import unittest
from app.util.response import Response


class TestResponse(unittest.TestCase):

    def test_response_ok(self):
        """
        Success response test.
        """
        data = {"key": "value"}
        response = Response.ok(data)

        self.assertTrue(response.sucess)
        self.assertEqual(response.data, data)
        self.assertIsNone(response.error)

    def test_response_fail(self):
        """
        Failure response test.
        """
        error_message = "Something went wrong"
        response = Response.fail(error_message)

        self.assertFalse(response.sucess)
        self.assertEqual(response.error, error_message)
        self.assertIsNone(response.data)


if __name__ == "__main__":
    unittest.main()
