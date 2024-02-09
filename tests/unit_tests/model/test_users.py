import pytest
from datetime import datetime, timezone
from app.model.users import Users
from uuid import uuid4


def test_users_creation_and_representation():
    now = datetime.now(timezone.utc)
    external_user_id = "external_user_123"

    user = Users(
        created_at=now,
        updated_at=now,
        externalUserId=external_user_id
    )

    expected_str = (
        f"User: (id:{user.id}, created_at:{now}, updated_at:{now}, externalUserId:{external_user_id})"
    )
    assert str(user) == expected_str
    assert repr(user) == expected_str


def test_users_equality():
    external_user_id1 = "external_user_123"
    external_user_id2 = "external_user_456"

    user1 = Users(
        externalUserId=external_user_id1
    )
    user2 = Users(
        externalUserId=external_user_id1
    )
    user3 = Users(
        externalUserId=external_user_id2
    )

    # Even if externalUserId matches, users are unique by their id
    assert user1 != user2

    # Users with different externalUserId are definitely not equal
    assert user1 != user3

    # Testing with the same ID for both instances
    user2.id = user1.id
    assert user1 == user2


def test_users_hash():
    external_user_id = "external_user_123"

    user1 = Users(
        externalUserId=external_user_id
    )

    user2 = Users(
        externalUserId=external_user_id
    )

    # Hashes should differ due to different IDs
    assert hash(user1) != hash(user2)

    # Making IDs same to test hash equality based on externalUserId
    user2.id = user1.id
    assert hash(user1) == hash(user2)


if __name__ == '__main__':
    pytest.main()