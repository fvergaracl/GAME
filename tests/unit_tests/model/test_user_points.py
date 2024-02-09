import pytest
from datetime import datetime, timezone
from app.model.user_points import UserPoints
from uuid import uuid4


def test_user_points_creation_and_representation():
    now = datetime.now(timezone.utc)
    user_id = str(uuid4())
    task_id = str(uuid4())
    user_points = UserPoints(
        created_at=now,
        updated_at=now,
        points=100,
        data={"level": 1, "score": 1500},
        description="First level completion",
        userId=user_id,
        taskId=task_id
    )

    expected_str = (
        f"UserPoints (id={user_points.id}, created_at={now}, updated_at={now}, points=100, "
        f"data={{'level': 1, 'score': 1500}}, description=First level completion, userId={user_id}, taskId={task_id})"
    )
    assert str(user_points) == expected_str
    assert repr(user_points) == expected_str


def test_user_points_equality():
    user_id = str(uuid4())
    task_id = str(uuid4())
    user_points1 = UserPoints(
        points=100,
        data={"level": 2, "score": 2500},
        description="Second level achievement",
        userId=user_id,
        taskId=task_id
    )
    user_points2 = UserPoints(
        points=100,
        data={"level": 2, "score": 2500},
        description="Second level achievement",
        userId=user_id,
        taskId=task_id
    )
    # Assuming different IDs, equality checks all fields
    assert user_points1 != user_points2

    # Testing with the same ID for both instances
    user_points2.id = user_points1.id
    assert user_points1 == user_points2


def test_user_points_hash():
    user_id = str(uuid4())
    task_id = str(uuid4())
    user_points1 = UserPoints(
        points=200,
        data={"level": 3, "achievements": ["win", "fastest_time"]},
        description="Third level special",
        userId=user_id,
        taskId=task_id
    )

    user_id_2 = str(uuid4())
    task_id_2 = str(uuid4())
    user_points2 = UserPoints(
        points=200,
        data={"level": 3, "achievements": ["win", "fastest_time"]},
        description="Third level special",
        userId=user_id_2,
        taskId=task_id_2
    )

    # Even if all attributes are the same, different IDs mean different objects
    assert hash(user_points1) != hash(user_points2)

    # Testing hash equality with the same ID
    user_points2.id = user_points1.id
    user_points2.userId = user_points1.userId
    user_points2.taskId = user_points1.taskId
    assert hash(user_points1) == hash(user_points2)


if __name__ == "__main__":
    pytest.main()
