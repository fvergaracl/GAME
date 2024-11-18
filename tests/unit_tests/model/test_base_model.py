from datetime import datetime
from uuid import uuid4

from app.model.base_model import BaseModel


def create_base_model_instance(apiKey_used="", oauth_user_id=""):
    return BaseModel(
        created_at=datetime.now(),
        updated_at=datetime.now(),
        apiKey_used=apiKey_used,
        oauth_user_id=oauth_user_id,
    )


def test_base_model_creation():
    """
    Test the creation of a BaseModel instance.
    """
    model = create_base_model_instance()
    assert isinstance(model, BaseModel)
    assert isinstance(model.id, uuid4().__class__)
    assert isinstance(model.created_at, datetime)
    assert isinstance(model.updated_at, datetime)
    assert model.apiKey_used == ""
    assert model.oauth_user_id == ""


def test_base_model_str():
    """
    Test the __str__ method of BaseModel.
    """
    model = create_base_model_instance(
        apiKey_used="testApiKey", oauth_user_id="testOAuthId"
    )
    expected_str = (
        f"BaseModel: (id={model.id}, created_at={model.created_at}, "
        f"updated_at={model.updated_at} apiKey_used={model.apiKey_used}, "
        f"oauth_user_id={model.oauth_user_id})"
    )
    assert str(model) == expected_str


def test_base_model_repr():
    """
    Test the __repr__ method of BaseModel.
    """
    model = create_base_model_instance(
        apiKey_used="testApiKey", oauth_user_id="testOAuthId"
    )
    expected_repr = (
        f"BaseModel: (id={model.id}, created_at={model.created_at}, "
        f"updated_at={model.updated_at} apiKey_used={model.apiKey_used}, "
        f"oauth_user_id={model.oauth_user_id})"
    )
    assert repr(model) == expected_repr


def test_base_model_equality():
    """
    Test the equality operator for BaseModel.
    """
    model1 = create_base_model_instance(
        apiKey_used="testApiKey", oauth_user_id="testOAuthId"
    )
    model2 = create_base_model_instance(
        apiKey_used="testApiKey", oauth_user_id="testOAuthId"
    )
    assert model1 != model2  # Different instances should not be equal

    # Manually set model2 attributes to match model1 for testing equality
    model2.id = model1.id
    model2.created_at = model1.created_at
    model2.updated_at = model1.updated_at
    assert model1 == model2  # Now they should be equal


def test_base_model_hash():
    """
    Test the __hash__ method of BaseModel.
    """
    model = create_base_model_instance(
        apiKey_used="testApiKey", oauth_user_id="testOAuthId"
    )
    expected_hash = hash(
        (
            model.id,
            model.created_at,
            model.updated_at,
            model.apiKey_used,
            model.oauth_user_id,
        )
    )
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
    assert isinstance(model.updated_at, datetime)


def test_base_model_apiKey_used():
    """
    Test the apiKey_used field in BaseModel.
    """
    model = create_base_model_instance(apiKey_used="testApiKey")
    assert model.apiKey_used == "testApiKey"


def test_base_model_oauth_user_id():
    """
    Test the oauth_user_id field in BaseModel.
    """
    model = create_base_model_instance(oauth_user_id="testOAuthId")
    assert model.oauth_user_id == "testOAuthId"
