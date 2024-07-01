from datetime import datetime
from uuid import uuid4
from app.model.user_actions import UserActions


def create_user_actions_instance():
    return UserActions(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        typeAction="Test Action",
        data={"key1": "value1", "key2": "value2"},
        description="Test description",
        userId=str(uuid4())
    )


def test_user_actions_creation():
    """
    Test the creation of a UserActions instance.
    """
    user_actions = create_user_actions_instance()
    assert isinstance(user_actions, UserActions)
    assert isinstance(user_actions.id, str)
    assert isinstance(user_actions.created_at, datetime)
    assert isinstance(user_actions.updated_at, datetime)
    assert user_actions.typeAction == "Test Action"
    assert user_actions.data == {"key1": "value1", "key2": "value2"}
    assert user_actions.description == "Test description"
    assert isinstance(user_actions.userId, str)


def test_user_actions_str():
    """
    Test the __str__ method of UserActions.
    """
    user_actions = create_user_actions_instance()
    expected_str = (
        f"UserActions (id={user_actions.id}, created_at={user_actions.created_at}"
        f", updated_at={user_actions.updated_at}, typeAction={user_actions.typeAction}, "
        f"data={user_actions.data}, description={user_actions.description}, "
        f"userId={user_actions.userId})"
    )
    assert str(user_actions) == expected_str


def test_user_actions_repr():
    """
    Test the __repr__ method of UserActions.
    """
    user_actions = create_user_actions_instance()
    expected_repr = (
        f"UserActions (id={user_actions.id}, created_at={user_actions.created_at}, "
        f"updated_at={user_actions.updated_at}, typeAction={user_actions.typeAction}, "
        f"data={user_actions.data}, description={user_actions.description}, "
        f"userId={user_actions.userId})"
    )
    assert repr(user_actions) == expected_repr


def test_user_actions_equality():
    """
    Test the equality operator for UserActions.
    """
    user_actions1 = create_user_actions_instance()
    user_actions2 = create_user_actions_instance()
    assert user_actions1 != user_actions2
    user_actions2.id = user_actions1.id
    user_actions2.typeAction = user_actions1.typeAction
    user_actions2.data = user_actions1.data
    user_actions2.description = user_actions1.description
    user_actions2.userId = user_actions1.userId
    assert user_actions1 == user_actions2


def test_user_actions_hash():
    """
    Test the __hash__ method of UserActions.
    """
    user_actions = create_user_actions_instance()
    expected_hash = hash((
        user_actions.typeAction, user_actions.make_hashable(user_actions.data),
        user_actions.description, user_actions.userId
    ))
    assert hash(user_actions) == expected_hash


def test_user_actions_make_hashable():
    """
    Test the make_hashable method of UserActions.
    """
    user_actions = create_user_actions_instance()
    original_data = {"key1": "value1", "key2": [
        "list_item1", {"nested_key": "nested_value"}]}
    expected_hashable_data = (
        ("key1", "value1"),
        ("key2", ("list_item1", (("nested_key", "nested_value"),)))
    )
    assert user_actions.make_hashable(original_data) == expected_hashable_data
