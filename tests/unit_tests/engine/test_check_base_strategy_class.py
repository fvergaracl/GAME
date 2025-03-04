import unittest
from unittest.mock import patch

from app.engine.check_base_strategy_class import check_class_methods_and_variables


class TestCheckClassMethodsAndVariables(unittest.TestCase):

    class FullClass:
        """A class with all required methods and variables."""

        strategy_name = "Test Strategy"
        strategy_description = "Description"
        strategy_name_slug = "test-strategy"
        strategy_version = "v1"
        variable_basic_points = 10
        variable_bonus_points = 5

        def get_strategy_id(self):
            pass

        def get_strategy_name(self):
            pass

        def get_strategy_description(self):
            pass

        def get_strategy_name_slug(self):
            pass

        def get_strategy_version(self):
            pass

        def get_variable_basic_points(self):
            pass

        def get_variable_bonus_points(self):
            pass

        def set_variables(self, variables):
            pass

        def get_variables(self):
            pass

        def get_variable(self, name):
            pass

        def set_variable(self, name, value):
            pass

        def get_strategy(self):
            pass

        def calculate_points(self):
            pass

        def generate_logic_graph(self):
            pass

    class IncompleteClass:
        """A class missing some methods and variables."""

        strategy_name = "Test Strategy"
        variable_basic_points = 10

        def get_strategy_name(self):
            pass

        def calculate_points(self):
            pass

    @patch("builtins.print")
    def test_class_with_all_methods_and_variables(self, mock_print):
        """
        Test that a class with all required methods and variables passes.
        """
        result = check_class_methods_and_variables(self.FullClass, debug=True)
        self.assertTrue(result)

        mock_print.assert_any_call("[+] All methods are present.")
        mock_print.assert_any_call("[+] All variables are present.")

    @patch("builtins.print")
    def test_class_missing_some_methods_and_variables(self, mock_print):
        """
        Test that a class missing some methods and variables fails.
        """
        result = check_class_methods_and_variables(self.IncompleteClass, debug=True)
        self.assertFalse(result)

        expected_missing_methods = "Missing methods: ['get_strategy_id', 'get_strategy_description', 'get_strategy_name_slug', 'get_strategy_version', 'get_variable_basic_points', 'get_variable_bonus_points', 'set_variables', 'get_variables', 'get_variable', 'set_variable', 'get_strategy', 'generate_logic_graph']"  # noqa
        expected_missing_variables = "Missing variables: ['strategy_description', 'strategy_name_slug', 'strategy_version']"  # noqa

        print(f"Print calls: " f"{[call.args for call in mock_print.call_args_list]}")

        mock_print.assert_any_call(expected_missing_methods)
        mock_print.assert_any_call(expected_missing_variables)


if __name__ == "__main__":
    unittest.main()
