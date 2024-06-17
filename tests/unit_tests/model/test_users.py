from datetime import datetime
from uuid import uuid4
from app.model.users import Users


def create_user_instance():
    return Users(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        externalUserId="external_user_123"
    )


def test_user_creation():
    """
    Test the creation of a Users instance.
    """
    user = create_user_instance()
    assert isinstance(user, Users)
    assert isinstance(user.id, str)
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)
    assert user.externalUserId == "external_user_123"


def test_user_str():
    """
    Test the __str__ method of Users.
    """
    user = create_user_instance()
    expected_str = (
        f"User: (id:{user.id}, created_at:{user.created_at}, "
        f"updated_at:{user.updated_at}, "
        f"externalUserId:{user.externalUserId})"
    )
    assert str(user) == expected_str


def test_user_repr():
    """
    Test the __repr__ method of Users.
    """
    user = create_user_instance()
    expected_repr = (
        f"User: (id:{user.id}, created_at:{user.created_at}, "
        f"updated_at:{user.updated_at}, "
        f"externalUserId:{user.externalUserId})"
    )
    assert repr(user) == expected_repr


def test_user_equality():
    """
    Test the equality operator for Users.
    """
    user1 = create_user_instance()
    user2 = create_user_instance()
    assert user1 != user2
    user2.id = user1.id
    user2.externalUserId = user1.externalUserId
    assert user1 == user2


def test_user_hash():
    """
    Test the __hash__ method of Users.
    """
    user = create_user_instance()
    expected_hash = hash((user.id, user.externalUserId))
    assert hash(user) == expected_hash
