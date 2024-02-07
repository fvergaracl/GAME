import pytest
from uuid import UUID
# Asegúrate de importar correctamente tu clase BaseModel
from app.model.base_model import BaseModel


def test_base_model_instantiation():
    model_instance = BaseModel()
    assert isinstance(model_instance.id, UUID)
    assert model_instance.created_at is not None
    assert model_instance.updated_at is not None


def test_base_model_equality():
    model_instance1 = BaseModel()
    model_instance2 = BaseModel()
    assert model_instance1 != model_instance2

    # Simular que model_instance2 es igual a model_instance1
    model_instance2.id = model_instance1.id
    model_instance2.created_at = model_instance1.created_at
    model_instance2.updated_at = model_instance1.updated_at
    assert model_instance1 == model_instance2


def test_base_model_ordering():
    model_instance1 = BaseModel()
    model_instance2 = BaseModel()
    assert model_instance1 != model_instance2
    assert (model_instance1 < model_instance2) or (
        model_instance1 > model_instance2)


def test_base_model_representation():
    model_instance = BaseModel()
    str_representation = (
        f"BaseModel: {model_instance.id}, {model_instance.created_at}, "
        "{model_instance.updated_at}"
    )
    assert str(model_instance) == str_representation
    assert repr(model_instance) == str_representation


def test_base_model_hash():
    model_instance = BaseModel()
    assert isinstance(hash(model_instance), int)


@pytest.mark.parametrize("model_instance1,model_instance2,expected", [
    (BaseModel(), BaseModel(), False),
    (BaseModel(), "not_a_model_instance", False),
])
def test_base_model_inequality(model_instance1, model_instance2, expected):
    assert (model_instance1 != model_instance2) is expected
