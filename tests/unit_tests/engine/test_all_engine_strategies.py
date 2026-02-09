import unittest
from types import ModuleType
from unittest.mock import patch

import app.engine.all_engine_strategies as all_engine_strategies_module


class TestAllEngineStrategies(unittest.TestCase):
    def test_discovers_valid_strategies_and_filters_base_strategy(self):
        strategy_files = [
            "strategy_one.py",
            "strategy_two.py",
            "__init__.py",
            "base_strategy.py",
            "check_base_strategy_class.py",
            "all_engine_strategies.py",
            "notes.txt",
        ]

        class ValidStrategy:
            __module__ = "app.engine.strategy_one"

            def get_strategy_id(self):
                return "ValidStrategy"

        class BaseLikeStrategy:
            __module__ = "app.engine.strategy_one"

            def get_strategy_id(self):
                return "BaseStrategy"

        class ExternalClass:
            __module__ = "external.module"

            def get_strategy_id(self):
                return "ExternalClass"

        module_one = ModuleType("app.engine.strategy_one")
        module_one.ValidStrategy = ValidStrategy
        module_one.BaseLikeStrategy = BaseLikeStrategy
        module_one.ExternalClass = ExternalClass

        module_two = ModuleType("app.engine.strategy_two")
        module_two.ExternalClass = ExternalClass

        with patch.object(
            all_engine_strategies_module.os, "listdir", return_value=strategy_files
        ), patch.object(
            all_engine_strategies_module, "check_class_methods_and_variables"
        ) as mock_check_class, patch.object(
            all_engine_strategies_module, "importlib"
        ) as mock_importlib:
            mock_importlib.import_module.side_effect = lambda module_name: {
                "app.engine.strategy_one": module_one,
                "app.engine.strategy_two": module_two,
            }[module_name]
            mock_check_class.return_value = True
            result = all_engine_strategies_module.all_engine_strategies()

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].id, "strategy_one")
            self.assertEqual(result[0].get_strategy_id(), "ValidStrategy")
            mock_check_class.assert_any_call(ValidStrategy)
            mock_check_class.assert_any_call(BaseLikeStrategy)
            mock_importlib.import_module.assert_any_call("app.engine.strategy_one")
            mock_importlib.import_module.assert_any_call("app.engine.strategy_two")

    def test_returns_empty_when_no_strategy_files(self):
        strategy_files = [
            "__init__.py",
            "base_strategy.py",
            "check_base_strategy_class.py",
            "all_engine_strategies.py",
            "README.md",
        ]

        with patch.object(
            all_engine_strategies_module.os, "listdir", return_value=strategy_files
        ), patch.object(all_engine_strategies_module, "importlib") as mock_importlib:
            result = all_engine_strategies_module.all_engine_strategies()

            self.assertEqual(result, [])
            mock_importlib.import_module.assert_not_called()

    def test_removes_strategy_when_class_validation_fails(self):
        strategy_files = ["invalid_strategy.py"]

        class AInvalidStrategy:
            __module__ = "app.engine.invalid_strategy"

            def get_strategy_id(self):
                return "AInvalidStrategy"

        class BShouldNotBeChecked:
            __module__ = "app.engine.invalid_strategy"

            def get_strategy_id(self):
                return "BShouldNotBeChecked"

        module_invalid = ModuleType("app.engine.invalid_strategy")
        module_invalid.AInvalidStrategy = AInvalidStrategy
        module_invalid.BShouldNotBeChecked = BShouldNotBeChecked

        def check_side_effect(cls):
            return cls is not AInvalidStrategy

        with patch.object(
            all_engine_strategies_module.os, "listdir", return_value=strategy_files
        ), patch.object(
            all_engine_strategies_module, "check_class_methods_and_variables"
        ) as mock_check_class, patch.object(
            all_engine_strategies_module, "importlib"
        ) as mock_importlib:
            mock_importlib.import_module.return_value = module_invalid
            mock_check_class.side_effect = check_side_effect
            result = all_engine_strategies_module.all_engine_strategies()

            self.assertEqual(result, [])
            self.assertEqual(mock_check_class.call_count, 1)
            mock_check_class.assert_called_once_with(AInvalidStrategy)


if __name__ == "__main__":
    unittest.main()
