from uuid import uuid4
from datetime import datetime
from app.model.base_model import BaseModel


def test_base_model_instantiation():
    id_str = str(uuid4())
    created_at = datetime.now()
    updated_at = datetime.now()

    # Act
    base_model = BaseModel(
        id=id_str, created_at=created_at, updated_at=updated_at)

    # Assert
    assert str(base_model.id) == id_str
    assert base_model.created_at == created_at
    assert base_model.updated_at == updated_at
    assert base_model.__str__(
    ) == f"BaseModel: {id_str}, {created_at}, {updated_at}"
    assert base_model.__repr__(
    ) == f"BaseModel: {id_str}, {created_at}, {updated_at}"
    assert base_model == base_model
    assert hash(base_model) == hash((id_str, created_at, updated_at))
    assert base_model != "other object"
    assert not base_model < base_model
    assert base_model <= base_model
    assert not base_model > base_model
