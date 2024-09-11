import unittest
from app.util.are_variables_matching import are_variables_matching


class TestAreVariablesMatching(unittest.TestCase):
    def test_matching_variables(self):
        """
        Test when all key-value pairs in new_variables match those in
          old_variables.
        """
        new_variables = {'a': 1, 'b': 2}
        old_variables = {'a': 1, 'b': 2, 'c': 3}
        self.assertTrue(are_variables_matching(new_variables, old_variables))

    def test_non_matching_variables(self):
        """
        Test when there is at least one mismatched value.
        """
        new_variables = {'a': 1, 'b': 99}
        old_variables = {'a': 1, 'b': 2, 'c': 3}
        self.assertFalse(are_variables_matching(new_variables, old_variables))

    def test_key_not_in_old_variables(self):
        """
        Test when new_variables contains a key not present in old_variables.
        """
        new_variables = {'d': 4}
        old_variables = {'a': 1, 'b': 2}
        self.assertTrue(are_variables_matching(new_variables, old_variables))

    def test_empty_new_variables(self):
        """
        Test when new_variables is empty.
        """
        new_variables = {}
        old_variables = {'a': 1, 'b': 2}
        self.assertTrue(are_variables_matching(new_variables, old_variables))

    def test_non_dict_input(self):
        """
        Test when inputs are not dictionaries.
        """
        new_variables = ['a', 'b']
        old_variables = {'a': 1, 'b': 2}
        with self.assertRaises(ValueError):
            are_variables_matching(new_variables, old_variables)

    def test_none_input(self):
        """
        Test when inputs are None.
        """
        new_variables = None
        old_variables = {'a': 1}
        with self.assertRaises(ValueError):
            are_variables_matching(new_variables, old_variables)

    def test_type_mismatch_in_values(self):
        """
        Test when values have different types but same representation.
        """
        new_variables = {'a': '1'}
        old_variables = {'a': 1}
        self.assertFalse(are_variables_matching(new_variables, old_variables))

    def test_nested_dictionaries(self):
        """
        Test when values are nested dictionaries that match.
        """
        new_variables = {'a': {'x': 1}}
        old_variables = {'a': {'x': 1}, 'b': 2}
        self.assertTrue(are_variables_matching(new_variables, old_variables))

    def test_nested_dictionaries_mismatch(self):
        """
        Test when nested dictionaries do not match.
        """
        new_variables = {'a': {'x': 1}}
        old_variables = {'a': {'x': 2}, 'b': 2}
        self.assertFalse(are_variables_matching(new_variables, old_variables))

    def test_partial_key_match(self):
        """
        Test when old_variables has keys that partially match new_variables.
        """
        new_variables = {'ab': 1}
        old_variables = {'a': 1, 'b': 2}
        self.assertTrue(are_variables_matching(new_variables, old_variables))


if __name__ == '__main__':
    unittest.main()
