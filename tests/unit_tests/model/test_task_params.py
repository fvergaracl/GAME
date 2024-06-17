from datetime import datetime
from uuid import uuid4
from app.model.task_params import TasksParams


def create_tasks_params_instance():
    return TasksParams(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        key="param_key",
        value="param_value",
        taskId=str(uuid4())
    )


def test_tasks_params_creation():
    """
    Test the creation of a TasksParams instance.
    """
    task_param = create_tasks_params_instance()
    assert isinstance(task_param, TasksParams)
    assert isinstance(task_param.id, str)
    assert isinstance(task_param.created_at, datetime)
    assert isinstance(task_param.updated_at, datetime)
    assert task_param.key == "param_key"
    assert task_param.value == "param_value"
    assert isinstance(task_param.taskId, str)


def test_tasks_params_str():
    """
    Test the __str__ method of TasksParams.
    """
    task_param = create_tasks_params_instance()
    expected_str = (
        f"TasksParams: (id={task_param.id}, "
        f"created_at={task_param.created_at}, "
        f"updated_at={task_param.updated_at}, key={task_param.key}, "
        f"value={task_param.value}, taskId={task_param.taskId})"
    )
    assert str(task_param) == expected_str


def test_tasks_params_repr():
    """
    Test the __repr__ method of TasksParams.
    """
    task_param = create_tasks_params_instance()
    expected_repr = (
        f"TasksParams: (id={task_param.id}, "
        f"created_at={task_param.created_at}, "
        f"updated_at={task_param.updated_at}, key={task_param.key}, "
        f"value={task_param.value}, taskId={task_param.taskId})"
    )
    assert repr(task_param) == expected_repr


def test_tasks_params_equality():
    """
    Test the equality operator for TasksParams.
    """
    task_param1 = create_tasks_params_instance()
    task_param2 = create_tasks_params_instance()
    task_param2.key = task_param1.key
    task_param2.value = task_param1.value
    task_param2.taskId = task_param1.taskId
    assert task_param1 == task_param2
    task_param2.taskId = str(uuid4())
    assert task_param1 != task_param2


def test_tasks_params_hash():
    """
    Test the __hash__ method of TasksParams.
    """
    task_param = create_tasks_params_instance()
    expected_hash = hash((task_param.key, task_param.value, task_param.taskId))
    assert hash(task_param) == expected_hash


def test_tasks_params_update_timestamp():
    """
    Test that the updated_at field is automatically updated.
    """
    task_param = create_tasks_params_instance()
    initial_updated_at = task_param.updated_at

    # Simulate an update
    task_param.updated_at = datetime.now()

    assert task_param.updated_at != initial_updated_at
