import unittest

# Assuming the check_role function is defined here
from app.util.check_role import check_role


class TestCheckRole(unittest.TestCase):

    def test_role_present(self):
        """
        Test when the role is present in the token.
        """
        token_decoded = {
            "resource_access": {"account": {"roles": ["admin", "creator", "user"]}}
        }
        self.assertTrue(check_role(token_decoded, "creator"))

    def test_role_not_present(self):
        """
        Test when the role is not present in the token.
        """
        token_decoded = {"resource_access": {"account": {"roles": ["admin", "user"]}}}
        self.assertFalse(check_role(token_decoded, "creator"))

    def test_no_resource_access(self):
        """
        Test when 'resource_access' is missing in the token.
        """
        token_decoded = {"some_other_key": {}}
        self.assertFalse(check_role(token_decoded, "creator"))

    def test_no_account_in_resource_access(self):
        """
        Test when 'account' is missing in 'resource_access'.
        """
        token_decoded = {
            "resource_access": {"other_service": {"roles": ["admin", "creator"]}}
        }
        self.assertFalse(check_role(token_decoded, "creator"))

    def test_no_roles_in_account(self):
        """
        Test when 'roles' is missing in 'account'.
        """
        token_decoded = {"resource_access": {"account": {}}}
        self.assertFalse(check_role(token_decoded, "creator"))

    def test_role_not_in_token(self):
        """
        Test when the required role is not in the token.
        """
        token_decoded = {"resource_access": {"account": {"roles": ["admin", "user"]}}}
        self.assertFalse(check_role(token_decoded, "creator"))

    def test_token_decoded_not_dict(self):
        """
        Test when the token_decoded is not a dictionary.
        """
        token_decoded = "this_is_a_string"
        self.assertFalse(check_role(token_decoded, "creator"))

    def test_token_empty(self):
        """
        Test when the token is empty.
        """
        token_decoded = {}
        self.assertFalse(check_role(token_decoded, "creator"))

    def test_role_is_none(self):
        """
        Test when the role is None.
        """
        token_decoded = {
            "resource_access": {"account": {"roles": ["admin", "creator"]}}
        }
        self.assertFalse(check_role(token_decoded, None))


if __name__ == "__main__":
    unittest.main()
