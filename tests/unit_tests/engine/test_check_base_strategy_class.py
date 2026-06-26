import unittest

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

    def test_class_with_all_methods_and_variables(self):
        """
        Test that a class with all required methods and variables passes.
        """
        with self.assertLogs(
            "app.engine.check_base_strategy_class", level="INFO"
        ) as captured:
            result = check_class_methods_and_variables(self.FullClass, debug=True)
        self.assertTrue(result)

        joined = "\n".join(captured.output)
        self.assertIn("All methods are present.", joined)
        self.assertIn("All variables are present.", joined)

    def test_class_missing_some_methods_and_variables(self):
        """
        Test that a class missing some methods and variables fails.
        """
        with self.assertLogs(
            "app.engine.check_base_strategy_class", level="WARNING"
        ) as captured:
            result = check_class_methods_and_variables(self.IncompleteClass, debug=True)
        self.assertFalse(result)

        joined = "\n".join(captured.output)
        self.assertIn("Missing methods:", joined)
        self.assertIn("get_strategy_id", joined)
        self.assertIn("get_strategy_description", joined)
        self.assertIn("Missing variables:", joined)
        self.assertIn("strategy_description", joined)
        self.assertIn("strategy_name_slug", joined)
        self.assertIn("strategy_version", joined)


if __name__ == "__main__":
    unittest.main()
