import unittest
from unittest.mock import patch

import app.engine.all_engine_strategies as all_engine_strategies_module
from app.engine import strategy_registry


class _RegistryReset:
    """Save and restore the strategy registry around a test."""

    def __enter__(self):
        self._saved = dict(strategy_registry._REGISTRY)
        self._saved_loaded = strategy_registry._external_loaded
        strategy_registry._REGISTRY.clear()
        strategy_registry._external_loaded = True  # skip entry-point lookup
        return self

    def __exit__(self, exc_type, exc, tb):
        strategy_registry._REGISTRY.clear()
        strategy_registry._REGISTRY.update(self._saved)
        strategy_registry._external_loaded = self._saved_loaded
        return False


def _make_valid_strategy_class(name: str):
    cls = type(name, (), {})
    return cls


class TestAllEngineStrategies(unittest.TestCase):
    def test_returns_instances_for_registered_strategies(self):
        with _RegistryReset():
            ValidA = _make_valid_strategy_class("ValidA")
            ValidB = _make_valid_strategy_class("ValidB")
            strategy_registry.register_strategy(id="alpha")(ValidA)
            strategy_registry.register_strategy(id="beta")(ValidB)

            with patch.object(
                all_engine_strategies_module,
                "check_class_methods_and_variables",
                return_value=True,
            ), patch.object(
                all_engine_strategies_module,
                "_discover_strategy_modules",
            ):
                result = all_engine_strategies_module.all_engine_strategies()

            ids = sorted(s.id for s in result)
            self.assertEqual(ids, ["alpha", "beta"])
            self.assertIsInstance(result[0], (ValidA, ValidB))

    def test_skips_classes_that_fail_validation(self):
        with _RegistryReset():
            Invalid = _make_valid_strategy_class("Invalid")
            Valid = _make_valid_strategy_class("Valid")
            strategy_registry.register_strategy(id="bad")(Invalid)
            strategy_registry.register_strategy(id="good")(Valid)

            def check_side_effect(cls):
                return cls is Valid

            with patch.object(
                all_engine_strategies_module,
                "check_class_methods_and_variables",
                side_effect=check_side_effect,
            ), patch.object(
                all_engine_strategies_module,
                "_discover_strategy_modules",
            ):
                result = all_engine_strategies_module.all_engine_strategies()

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].id, "good")

    def test_returns_empty_when_registry_is_empty(self):
        with _RegistryReset():
            with patch.object(
                all_engine_strategies_module,
                "_discover_strategy_modules",
            ):
                result = all_engine_strategies_module.all_engine_strategies()

            self.assertEqual(result, [])

    def test_register_strategy_rejects_duplicate_id(self):
        with _RegistryReset():
            A = _make_valid_strategy_class("A")
            B = _make_valid_strategy_class("B")
            strategy_registry.register_strategy(id="dup")(A)
            with self.assertRaises(ValueError):
                strategy_registry.register_strategy(id="dup")(B)

    def test_register_strategy_is_idempotent_for_same_class(self):
        with _RegistryReset():
            A = _make_valid_strategy_class("A")
            decorate = strategy_registry.register_strategy(id="same")
            decorate(A)
            decorate(A)
            self.assertIs(strategy_registry._REGISTRY["same"], A)

    def test_register_strategy_rejects_empty_id(self):
        with self.assertRaises(ValueError):
            strategy_registry.register_strategy(id="")

    def test_discovery_registers_all_builtin_strategies(self):
        all_engine_strategies_module._discovery_done = False
        all_engine_strategies_module._discover_strategy_modules()
        registered = strategy_registry.registered_strategies()
        for expected_id in (
            "default",
            "constantEffortStrategy",
            "greencrowdStrategy",
            "greengageStrategy",
            "socio_bee",
            "getis_ord_gi_star",
        ):
            self.assertIn(expected_id, registered)

    def test_discovery_skips_infrastructure_modules(self):
        all_engine_strategies_module._discovery_done = False
        with patch.object(
            all_engine_strategies_module.importlib, "import_module"
        ) as mock_import:
            mock_import.return_value = __import__("app.engine", fromlist=["*"])
            all_engine_strategies_module._discover_strategy_modules()
            imported = {call.args[0] for call in mock_import.call_args_list}

        for skipped in (
            "app.engine.base_strategy",
            "app.engine.check_base_strategy_class",
            "app.engine.strategy_registry",
            "app.engine.all_engine_strategies",
        ):
            self.assertNotIn(skipped, imported)

    def test_discovery_tolerates_a_broken_module(self):
        all_engine_strategies_module._discovery_done = False
        real_import = all_engine_strategies_module.importlib.import_module

        def fake_import(name, *args, **kwargs):
            if name == "app.engine.default":
                raise RuntimeError("boom")
            return real_import(name, *args, **kwargs)

        with patch.object(
            all_engine_strategies_module.importlib,
            "import_module",
            side_effect=fake_import,
        ):
            # Should not raise even though one strategy module fails to import.
            all_engine_strategies_module._discover_strategy_modules()


if __name__ == "__main__":
    unittest.main()
