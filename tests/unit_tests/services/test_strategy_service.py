import unittest
from unittest.mock import MagicMock, patch

from app.core.exceptions import NotFoundError
from app.services.strategy_service import StrategyService


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


if __name__ == "__main__":
    unittest.main()
