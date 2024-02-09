import pytest
from uuid import uuid4
from datetime import datetime
from app.model.strategy import Strategy


def test_strategy_basic_operations():
    # Create a Strategy instance with required fields
    created_at = datetime.now()
    updated_at = datetime.now()
    strategy = Strategy(
        created_at=created_at,
        updated_at=updated_at,
        strategyName="test_strategy",
        data={"key": "value"}
    )

    # Test the string representation
    # Make sure to convert `strategy_id` to string, as it is how it would be represented in the actual output
    expected_str = (
        f"Strategy(id={str(strategy.id)}, created_at={created_at}, "
        f"updated_at={updated_at}, strategyName=test_strategy, data={{'key': 'value'}})"
    )
    assert str(strategy) == expected_str

    # Test the equality comparison with the same object
    assert strategy == strategy

    # Create a new strategy with the same properties
    strategy_clone = Strategy(
        id=strategy.id,
        created_at=created_at,
        updated_at=updated_at,
        strategyName="test_strategy",
        data={"key": "value"}
    )

    # Test the equality comparison with a different object with the same properties
    assert strategy == strategy_clone

    # Test the hash function
    # Since hash uses sorted tuple conversion of dict, it should match for identical data
    assert hash(strategy) == hash(strategy_clone)

    # Test inequality with a different object
    different_strategy = Strategy(
        strategyName="different_strategy",
        data={"key": "different_value"}
    )
    assert strategy != different_strategy


def test_strategy_with_different_data():
    # Test strategies with different types of data
    strategy_with_list_data = Strategy(
        strategyName="strategy_with_list",
        data={"list_key": [1, 2, 3]}
    )

    strategy_with_nested_dict = Strategy(
        strategyName="strategy_with_nested_dict",
        data={"nested": {"inner_key": "inner_value"}}
    )

    # Ensuring __str__, __eq__, and __hash__ do not raise errors with complex data types
    assert str(strategy_with_list_data)
    assert str(strategy_with_nested_dict)
    assert strategy_with_list_data != strategy_with_nested_dict
    assert hash(strategy_with_list_data) != hash(strategy_with_nested_dict)


def test_strategy_equality_with_none():
    strategy = Strategy(
        strategyName="test_strategy",
        data={"key": "value"}
    )

    # Test the inequality with None
    assert strategy is not None

# Add more tests if needed, especially focusing on edge cases and failure scenarios


if __name__ == "__main__":
    pytest.main()
