import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import NotFoundError
from app.services.strategy_service import (
    CUSTOM_STRATEGY_PREFIX,
    StrategyService,
    is_custom_strategy_id,
    parse_custom_strategy_id,
)


class FakeStrategyDefault:
    id = "default"

    def get_strategy_name(self):
        return "Default Strategy"

    def get_strategy_description(self):
        return "Default description"

    def get_strategy_version(self):
        return "1.0.0"

    def get_variables(self):
        return {"basic_points": 1}

    def _generate_hash_of_calculate_points(self):
        return "hash-default"


class FakeStrategySocioBee:
    id = "socio_bee"

    def get_strategy_name(self):
        return "Socio Bee"

    def get_strategy_description(self):
        return "Socio Bee description"

    def get_strategy_version(self):
        return "2.0.0"

    def get_variables(self):
        return {"bonus": 2}

    def _generate_hash_of_calculate_points(self):
        return "hash-socio"


class TestStrategyService(unittest.TestCase):
    def setUp(self):
        self.service = StrategyService()

    def test_init_sets_base_repository_as_none(self):
        self.assertIsNone(self.service._repository)

    @patch(
        "app.services.strategy_service.all_engine_strategies",
        return_value=[FakeStrategyDefault(), FakeStrategySocioBee()],
    )
    async def test_list_all_strategies_returns_cleaned_strategy_payloads(
        self,
        _mock_all_engine_strategies,
    ):
        result = await self.service.list_all_strategies()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "default")
        self.assertEqual(result[0]["name"], "Default Strategy")
        self.assertEqual(result[0]["description"], "Default description")
        self.assertEqual(result[0]["version"], "1.0.0")
        self.assertEqual(result[0]["variables"], {"basic_points": 1})
        self.assertEqual(result[0]["hash_version"], "hash-default")
        self.assertEqual(result[1]["id"], "socio_bee")
        self.assertEqual(result[1]["name"], "Socio Bee")

    async def test_get_strategy_by_id_returns_matching_strategy(self):
        expected = {"id": "default", "name": "Default"}
        self.service.list_all_strategies = MagicMock(
            return_value=[expected, {"id": "other", "name": "Other"}]
        )

        result = await self.service.get_strategy_by_id("default")

        self.assertEqual(result, expected)

    async def test_get_strategy_by_id_raises_not_found_when_missing(self):
        self.service.list_all_strategies = MagicMock(
            return_value=[{"id": "default"}]
        )

        with self.assertRaises(NotFoundError) as context:
            await self.service.get_strategy_by_id("missing")

        self.assertEqual(
            context.exception.detail, "Strategy not found with id: missing"
        )

    @patch(
        "app.services.strategy_service.all_engine_strategies",
        return_value=[FakeStrategyDefault(), FakeStrategySocioBee()],
    )
    async def test_get_class_by_id_returns_strategy_instance(
        self,
        _mock_all_engine_strategies,
    ):
        result = await self.service.get_Class_by_id("socio_bee")

        self.assertIsInstance(result, FakeStrategySocioBee)

    @patch(
        "app.services.strategy_service.all_engine_strategies",
        return_value=[FakeStrategyDefault()],
    )
    async def test_get_class_by_id_raises_not_found_when_missing(
        self,
        _mock_all_engine_strategies,
    ):
        with self.assertRaises(NotFoundError) as context:
            await self.service.get_Class_by_id("missing")

        self.assertEqual(
            context.exception.detail, "Strategy not found with id: missing"
        )


class TestCustomStrategyPrefix(unittest.TestCase):
    def test_prefix_helpers_round_trip_an_id(self):
        custom_id = f"{CUSTOM_STRATEGY_PREFIX}abc-123"
        self.assertTrue(is_custom_strategy_id(custom_id))
        self.assertEqual(parse_custom_strategy_id(custom_id), "abc-123")

    def test_builtin_ids_are_not_custom(self):
        self.assertFalse(is_custom_strategy_id("default"))
        self.assertFalse(is_custom_strategy_id(""))
        self.assertFalse(is_custom_strategy_id(None))


class TestStrategyServiceCompatLayer(unittest.IsolatedAsyncioTestCase):
    async def test_get_class_by_id_refuses_custom_prefix(self):
        service = StrategyService()
        with self.assertRaises(NotFoundError):
            service.get_Class_by_id(f"{CUSTOM_STRATEGY_PREFIX}some-uuid")

    async def test_resolve_routes_builtin_to_registry(self):
        service = StrategyService()
        instance = MagicMock()
        instance.id = "default"
        with patch(
            "app.services.strategy_service.all_engine_strategies",
            return_value=[instance],
        ):
            resolved = await service.resolve("default")

        self.assertEqual(resolved["kind"], "BUILT_IN")
        self.assertIs(resolved["instance"], instance)

    async def test_resolve_routes_custom_to_definition_service(self):
        fake_definition = MagicMock()
        fake_definition.type = "DSL_FULL"
        definition_service = MagicMock()
        definition_service.get_strategy = AsyncMock(
            return_value=fake_definition
        )

        service = StrategyService(
            strategy_definition_service=definition_service
        )
        resolved = await service.resolve(
            f"{CUSTOM_STRATEGY_PREFIX}uuid-1", realmId="realm-a"
        )

        definition_service.get_strategy.assert_awaited_once_with(
            id="uuid-1", realmId="realm-a"
        )
        self.assertEqual(resolved["kind"], "DSL_FULL")
        self.assertIs(resolved["definition"], fake_definition)

    async def test_resolve_custom_without_dsl_service_raises(self):
        service = StrategyService(strategy_definition_service=None)
        with self.assertRaises(NotFoundError):
            await service.resolve(
                f"{CUSTOM_STRATEGY_PREFIX}uuid-1", realmId="realm-a"
            )


if __name__ == "__main__":
    unittest.main()
