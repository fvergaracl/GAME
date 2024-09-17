from datetime import datetime
from uuid import uuid4

from app.model.tasks import Tasks


def create_tasks_instance():
    return Tasks(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        externalTaskId="task123",
        gameId=str(uuid4()),
        strategyId="default",
    )


def test_tasks_creation():
    """
    Test the creation of a Tasks instance.
    """
    task = create_tasks_instance()
    assert isinstance(task, Tasks)
    assert isinstance(task.id, str)
    assert isinstance(task.created_at, datetime)
    assert isinstance(task.updated_at, datetime)
    assert task.externalTaskId == "task123"
    assert isinstance(task.gameId, str)
    assert task.strategyId == "default"


def test_tasks_str():
    """
    Test the __str__ method of Tasks.
    """
    task = create_tasks_instance()
    expected_str = (
        f"Tasks(id={task.id}, created_at={task.created_at}, "
        f"updated_at={task.updated_at}, "
        f"externalTaskId={task.externalTaskId}, gameId={task.gameId}, "
        f"strategyId={task.strategyId}, status={task.status})"
    )
    assert str(task) == expected_str


def test_tasks_repr():
    """
    Test the __repr__ method of Tasks.
    """
    task = create_tasks_instance()
    expected_repr = (
        f"Tasks(id={task.id}, created_at={task.created_at}, "
        f"updated_at={task.updated_at}, "
        f"externalTaskId={task.externalTaskId}, gameId={task.gameId}, "
        f"strategyId={task.strategyId}, status={task.status})"
    )
    assert repr(task) == expected_repr


def test_tasks_equality():
    """
    Test the equality operator for Tasks.
    """
    task1 = create_tasks_instance()
    task2 = create_tasks_instance()
    task2.externalTaskId = task1.externalTaskId
    task2.gameId = task1.gameId
    task2.strategyId = task1.strategyId
    assert task1 != task2  # Different instances should not be equal
    task2.id = task1.id
    assert task1 == task2  # Same attributes should be equal


def test_tasks_hash():
    """
    Test the __hash__ method of Tasks.
    """
    task = create_tasks_instance()
    expected_hash = task.__hash__()
    assert task.__hash__() == expected_hash


def test_tasks_update_timestamp():
    """
    Test that the updated_at field is automatically updated.
    """
    task = create_tasks_instance()
    initial_updated_at = task.updated_at

    # Simulate an update
    task.updated_at = datetime.now()

    assert task.updated_at != initial_updated_at
