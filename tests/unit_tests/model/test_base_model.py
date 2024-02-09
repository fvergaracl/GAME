import pytest
from datetime import datetime, timezone
from sqlmodel import Field
from app.model.base_model import BaseModel
from uuid import UUID


class DerivedModel(BaseModel, table=True):
    """
    A derived model to test the inheritance capabilities of BaseModel.
    """
    name: str = Field(default="Test Name")


def test_base_model_instantiation():
    # Providing default values for created_at and updated_at for testing purposes
    now = datetime.now(timezone.utc)
    instance = BaseModel(created_at=now, updated_at=now)

    assert isinstance(instance.id, UUID)
    assert instance.created_at == now
    assert instance.updated_at == now


def test_derived_model_instantiation_and_attributes():
    derived_instance = DerivedModel()

    assert isinstance(derived_instance.id, UUID)
    assert derived_instance.name == "Test Name"
    assert derived_instance.created_at is None
    assert derived_instance.updated_at is None


def test_base_model_string_representation():
    now = datetime.now(timezone.utc)
    instance = BaseModel(created_at=now, updated_at=now)
    expected_str = f"BaseModel: (id={instance.id}, created_at={instance.created_at}, updated_at={instance.updated_at})"
    assert str(instance) == expected_str
    assert repr(instance) == expected_str


def test_base_model_equality():
    now = datetime.now(timezone.utc)
    instance1 = BaseModel(created_at=now, updated_at=now)
    instance2 = BaseModel(created_at=now, updated_at=now)

    # Initially, instances should not be equal because they have different IDs
    assert instance1 != instance2

    # Make IDs, created_at, and updated_at the same to test equality
    instance2.id = instance1.id
    assert instance1 == instance2


def test_base_model_hash():
    now = datetime.now(timezone.utc)
    instance1 = BaseModel(created_at=now, updated_at=now)
    instance2 = BaseModel(created_at=now, updated_at=now)

    # Hashes should be different due to different IDs
    assert hash(instance1) != hash(instance2)

    # Make IDs the same to test hash equality
    instance2.id = instance1.id
    assert hash(instance1) == hash(instance2)


if __name__ == "__main__":
    pytest.main()
