from datetime import datetime
from uuid import uuid4
from app.model.user_points import UserPoints


def create_user_points_instance():
    return UserPoints(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        points=100,
        caseName="Test Case",
        data={"key1": "value1", "key2": "value2"},
        description="Test description",
        userId=str(uuid4()),
        taskId=str(uuid4())
    )


def test_user_points_creation():
    """
    Test the creation of a UserPoints instance.
    """
    user_points = create_user_points_instance()
    assert isinstance(user_points, UserPoints)
    assert isinstance(user_points.id, str)
    assert isinstance(user_points.created_at, datetime)
    assert isinstance(user_points.updated_at, datetime)
    assert user_points.points == 100
    assert user_points.caseName == "Test Case"
    assert user_points.data == {"key1": "value1", "key2": "value2"}
    assert user_points.description == "Test description"
    assert isinstance(user_points.userId, str)
    assert isinstance(user_points.taskId, str)


def test_user_points_str():
    """
    Test the __str__ method of UserPoints.
    """
    user_points = create_user_points_instance()
    expected_str = (
        f"UserPoints (id={user_points.id}, created_at={user_points.created_at}"
        f", updated_at={user_points.updated_at}, points={user_points.points}, "
        f"caseName={user_points.caseName}, data={user_points.data}, "
        f"description={user_points.description}, userId={user_points.userId}, "
        f"taskId={user_points.taskId})"
    )
    assert str(user_points) == expected_str


def test_user_points_repr():
    """
    Test the __repr__ method of UserPoints.
    """
    user_points = create_user_points_instance()
    expected_repr = (
        f"UserPoints (id={user_points.id}, created_at={user_points.created_at}"
        f", updated_at={user_points.updated_at}, points={user_points.points}, "
        f"caseName={user_points.caseName}, data={user_points.data}, "
        f"description={user_points.description}, userId={user_points.userId}, "
        f"taskId={user_points.taskId})"
    )
    assert repr(user_points) == expected_repr


def test_user_points_equality():
    """
    Test the equality operator for UserPoints.
    """
    user_points1 = create_user_points_instance()
    user_points2 = create_user_points_instance()
    assert user_points1 != user_points2
    user_points2.id = user_points1.id
    user_points2.points = user_points1.points
    user_points2.caseName = user_points1.caseName
    user_points2.data = user_points1.data
    user_points2.description = user_points1.description
    user_points2.userId = user_points1.userId
    user_points2.taskId = user_points1.taskId
    assert user_points1 == user_points2


def test_user_points_hash():
    """
    Test the __hash__ method of UserPoints.
    """
    user_points = create_user_points_instance()
    expected_hash = hash((
        user_points.points, user_points.caseName,
        user_points.make_hashable(user_points.data), user_points.description,
        user_points.userId, user_points.taskId
    ))
    assert hash(user_points) == expected_hash


def test_user_points_make_hashable():
    """
    Test the make_hashable method of UserPoints.
    """
    user_points = create_user_points_instance()
    original_data = {"key1": "value1", "key2": [
        "list_item1", {"nested_key": "nested_value"}]}
    expected_hashable_data = (
        ("key1", "value1"),
        ("key2", ("list_item1", (("nested_key", "nested_value"),)))
    )
    assert user_points.make_hashable(original_data) == expected_hashable_data
