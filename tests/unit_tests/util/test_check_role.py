import unittest
from unittest.mock import patch

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

    def test_role_present_in_realm_access(self):
        """
        Test when the role is present in realm_access.roles.
        """
        token_decoded = {"realm_access": {"roles": ["admin", "creator"]}}
        self.assertTrue(check_role(token_decoded, "creator"))

    def test_role_present_in_top_level_roles(self):
        """
        Test when the role is present in top-level roles.
        """
        token_decoded = {"roles": ["admin", "creator"]}
        self.assertTrue(check_role(token_decoded, "creator"))

    def test_role_present_in_resource_access_client_id(self):
        """
        Test when the role is present in resource_access[KEYCLOAK_CLIENT_ID].roles.
        """
        token_decoded = {
            "resource_access": {
                "game-backend": {"roles": ["AdministratorGAME", "user"]},
                "other-client": {"roles": ["user"]},
            }
        }
        with patch.dict("os.environ", {"KEYCLOAK_CLIENT_ID": "game-backend"}):
            self.assertTrue(check_role(token_decoded, "AdministratorGAME"))

    def test_role_not_taken_from_other_clients(self):
        """
        Test that roles in non-configured clients are ignored.
        """
        token_decoded = {
            "resource_access": {
                "other-client": {"roles": ["AdministratorGAME"]},
            }
        }
        with patch.dict("os.environ", {"KEYCLOAK_CLIENT_ID": "game-backend"}):
            self.assertFalse(check_role(token_decoded, "AdministratorGAME"))


if __name__ == "__main__":
    unittest.main()
