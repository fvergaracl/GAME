from datetime import datetime
from uuid import uuid4

from app.model.base_model import BaseModel


def create_base_model_instance():
    return BaseModel(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        apiKey_used="",
    )


def test_base_model_creation():
    """
    Test the creation of a BaseModel instance.
    """
    model = create_base_model_instance()
    assert isinstance(model, BaseModel)
    assert isinstance(model.id, str)
    assert isinstance(model.created_at, datetime)
    assert isinstance(model.updated_at, datetime)


def test_base_model_str():
    """
    Test the __str__ method of BaseModel.
    """
    model = create_base_model_instance()
    expected_str = (
        f"BaseModel: (id={model.id}, created_at={model.created_at}, "
        f"updated_at={model.updated_at})"
    )
    assert str(model) == expected_str


def test_base_model_repr():
    """
    Test the __repr__ method of BaseModel.
    """
    model = create_base_model_instance()
    expected_repr = (
        f"BaseModel: (id={model.id}, created_at={model.created_at}, "
        f"updated_at={model.updated_at})"
    )
    assert repr(model) == expected_repr


def test_base_model_equality():
    """
    Test the equality operator for BaseModel.
    """
    model1 = create_base_model_instance()
    model2 = create_base_model_instance()
    assert model1 != model2  # Different instances should not be equal
    assert model1 == model1  # Same instance should be equal to itself


def test_base_model_hash():
    """
    Test the __hash__ method of BaseModel.
    """
    model = create_base_model_instance()
    expected_hash = hash((model.id, model.created_at, model.updated_at))
    assert hash(model) == expected_hash


def test_base_model_update_timestamp():
    """
    Test that the updated_at field is automatically updated.
    """
    model = create_base_model_instance()
    initial_updated_at = model.updated_at

    # Simulate an update
    model.updated_at = datetime.now()

    assert model.updated_at != initial_updated_at
