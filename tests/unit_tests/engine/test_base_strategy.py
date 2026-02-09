import pytest

from app.engine.base_strategy import BaseStrategy


def test_base_strategy_metadata_and_getters():
    strategy = BaseStrategy(
        strategy_name="base-name",
        strategy_description="base-description",
        strategy_name_slug="base-slug",
        strategy_version="1.2.3",
        variable_basic_points=7,
        variable_bonus_points=11,
    )

    assert strategy.get_strategy_id() == "BaseStrategy"
    assert strategy.get_strategy_name() == "base-name"
    assert strategy.get_strategy_description() == "base-description"
    assert strategy.get_strategy_name_slug() == "base-slug"
    assert strategy.get_strategy_version() == "1.2.3"
    assert strategy.get_variable_basic_points() == 7
    assert strategy.get_variable_bonus_points() == 11

    strategy_payload = strategy.get_strategy()
    assert strategy_payload["name"] == "base-name"
    assert strategy_payload["description"] == "base-description"
    assert strategy_payload["name_slug"] == "base-slug"
    assert strategy_payload["version"] == "1.2.3"
    assert strategy_payload["variables"]["variable_basic_points"] == 7
    assert strategy_payload["variables"]["variable_bonus_points"] == 11
    assert isinstance(strategy_payload["hash_version"], str)
    assert len(strategy_payload["hash_version"]) == 64


def test_base_strategy_variable_mutation_helpers():
    strategy = BaseStrategy(variable_basic_points=3, variable_bonus_points=5)

    changed = strategy.set_variables(
        {
            "variable_basic_points": 10,
            "variable_bonus_points": 20,
            "unknown_variable": 99,
        }
    )
    assert changed == ["variable_basic_points", "variable_bonus_points"]
    assert strategy.get_variables()["variable_basic_points"] == 10
    assert strategy.get_variables()["variable_bonus_points"] == 20

    assert strategy.get_variable("variable_basic_points") == 10
    assert strategy.get_variable("not_exists") is None

    assert strategy.set_variable("variable_bonus_points", 30) is True
    assert strategy.get_variable("variable_bonus_points") == 30
    assert strategy.set_variable("not_exists", 1) is False


@pytest.mark.asyncio
async def test_base_strategy_default_behaviour_methods():
    strategy = BaseStrategy(variable_basic_points=42)

    points = await strategy.calculate_points()
    assert points == 42
    assert strategy.simulate_strategy() is None

    dot = strategy.generate_logic_graph(format="svg")
    assert dot.format == "svg"
    assert "No logic graph available" in dot.source


def test_base_strategy_debug_print_only_when_enabled(capsys):
    strategy = BaseStrategy()
    strategy.debug_print("hidden")
    captured = capsys.readouterr()
    assert captured.out == ""

    strategy.debug = True
    strategy.debug_print("visible")
    captured = capsys.readouterr()
    assert "visible" in captured.out
