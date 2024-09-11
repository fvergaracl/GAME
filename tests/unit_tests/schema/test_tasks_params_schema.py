from app.schema.tasks_params_schema import (BaseTaskParams, CreateTaskParams,
                                            InsertTaskParams)


def test_base_task_params():
    """
    Test the BaseTaskParams model.

    The BaseTaskParams model is used as a base model for task parameters.

    The model has the following attributes:
    - key (str): Parameter key
    - value (str | int | float | bool): Parameter value
    """
    data = {"key": "param1", "value": 100}
    base_task_params = BaseTaskParams(**data)
    assert base_task_params.key == data["key"]
    assert base_task_params.value == data["value"].__str__()


def test_create_task_params():
    """
    Test the CreateTaskParams model.

    The CreateTaskParams model is used for creating task parameters.

    The model inherits attributes from BaseTaskParams.
    """
    data = {"key": "param2", "value": "test value"}
    create_task_params = CreateTaskParams(**data)
    assert create_task_params.key == data["key"]
    assert create_task_params.value == data["value"]

    example_data = CreateTaskParams.example()
    assert example_data["key"] == "variable_bonus_points"
    assert example_data["value"] == 20


def test_insert_task_params():
    """
    Test the InsertTaskParams model.

    The InsertTaskParams model is used for inserting task parameters.

    The model has the following attributes:
    - key (str): Parameter key
    - value (str | int | float | bool): Parameter value
    - taskId (str): Task ID
    """
    data = {"key": "param3", "value": 50.5, "taskId": "task123"}
    insert_task_params = InsertTaskParams(**data)
    assert insert_task_params.key == data["key"]
    assert insert_task_params.value == data["value"].__str__()
    assert insert_task_params.taskId == data["taskId"]
