from datetime import datetime
from uuid import uuid4
from app.schema.task_schema import (
    BaseTask, AsignPointsToExternalUserId, CreateTaskPost, FoundTask,
    FoundTasks, CreateTask, FindTask, CreateTaskPostSuccesfullyCreated,
    AssignedPointsToExternalUserId, TaskPointsResponseByUser, BaseUser,
    BaseUserFirstAction, TasksWithUsers, PostFindTask
)
from app.schema.games_params_schema import CreateGameParams
from app.schema.base_schema import SearchOptions
from app.schema.strategy_schema import Strategy
from app.schema.tasks_params_schema import CreateTaskParams


def test_base_task():
    """
    Test the BaseTask model.

    The BaseTask model is used as a base model for a task.

    The model has the following attributes:
    - externalTaskId (str): External task ID
    - gameId (UUID): Game ID
    """
    data = {
        "externalTaskId": "task123",
        "gameId": uuid4()
    }
    task = BaseTask(**data)
    assert task.externalTaskId == data["externalTaskId"]
    assert task.gameId == data["gameId"]


def test_asign_points_to_external_user_id():
    """
    Test the AsignPointsToExternalUserId model.

    The AsignPointsToExternalUserId model is used for assigning points to an
    external user ID.

    The model has the following attributes:
    - externalUserId (str): External user ID
    - data (Optional[dict]): Additional data
    """

    data = {
        "externalUserId": "user123",
        "data": {"key": "value"}
    }
    asign_points = AsignPointsToExternalUserId(**data)
    assert asign_points.externalUserId == data["externalUserId"]
    assert asign_points.data == data["data"]


def test_create_task_post():
    """
    Test the CreateTaskPost model.

    The CreateTaskPost model is used for creating a task.

    The model has the following attributes:
    - externalTaskId (str): External task ID
    - strategyId (Optional[str]): Strategy ID
    - params (Optional[List[CreateTaskParams]]): Task parameters

    """
    data = {
        "externalTaskId": "task123",
        "strategyId": "default",
        "params": [{"key": "var1", "value": 10}]
    }
    create_task = CreateTaskPost(**data)
    assert create_task.externalTaskId == data["externalTaskId"]
    assert create_task.strategyId == data["strategyId"]
    assert create_task.params[0].key == data["params"][0]["key"]
    assert create_task.params[0].value == data["params"][0]["value"].__str__()


def test_post_find_task():
    """
    Test the PostFindTask model.

    The PostFindTask model is used for finding tasks.

    The model inherits attributes from FindBase.
    """

    data = {
        "ordering": "asc",
        "page": 1,
        "page_size": 10
    }
    post_find_task = PostFindTask(**data)
    assert post_find_task.ordering == data["ordering"]
    assert post_find_task.page == data["page"]
    assert post_find_task.page_size == data["page_size"]


def test_found_task():
    """
    Test the FoundTask model.

    The FoundTask model is used for a found task.

    The model has the following attributes:
    - externalTaskId (str): External task ID
    - gameParams (Optional[List[CreateGameParams]]): Game parameters
    - taskParams (Optional[List[CreateTaskParams]]): Task parameters
    - strategy (Optional[Strategy]): Strategy
    """

    data = {
        "id": uuid4(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "externalTaskId": "task123",
        "gameParams": [CreateGameParams(key="var1", value=10)],
        "taskParams": [CreateTaskParams(key="var2", value=20)],
        "strategy": Strategy(
            id="strategy123",
            version="1.0",
            variables={"var1": 10}
        )
    }
    found_task = FoundTask(**data)
    assert found_task.externalTaskId == data["externalTaskId"]
    assert found_task.gameParams[0].key == data["gameParams"][0].key
    assert found_task.taskParams[0].key == data["taskParams"][0].key
    assert found_task.strategy.id == data["strategy"].id
    assert found_task.strategy.variables["var1"] == (
        data["strategy"].variables["var1"]
    )


def test_found_tasks():
    """
    Test the FoundTasks model.

    The FoundTasks model is used for found tasks.

    The model has the following attributes:
    - items (Optional[List[FoundTask]]): List of found tasks
    - search_options (Optional[SearchOptions]): Search options
    """
    data = {
        "items": [
            FoundTask(
                id=uuid4(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                externalTaskId="task123",
                gameParams=[CreateGameParams(key="var1", value=10)],
                taskParams=[CreateTaskParams(key="var2", value=20)],
                strategy=Strategy(
                    id="strategy123",
                    version="1.0",
                    variables={"var1": 10}
                )
            )
        ],
        "search_options": SearchOptions(
            ordering="asc",
            page=1,
            page_size=10,
            total_count=1
        )
    }
    found_tasks = FoundTasks(**data)
    assert found_tasks.items == data["items"]
    assert found_tasks.search_options == data["search_options"]


def test_create_task():
    """
    Test the CreateTask model.

    The CreateTask model is used for creating a task.

    The model has the following attributes:
    - gameId (str): Game ID
    """
    data = {
        "externalTaskId": "task123",
        "strategyId": "default",
        "params": [CreateTaskParams(key="var1", value=10)],
        "gameId": "game123"
    }
    create_task = CreateTask(**data)
    assert create_task.externalTaskId == data["externalTaskId"]
    assert create_task.strategyId == data["strategyId"]
    assert create_task.params[0].key == data["params"][0].key
    assert create_task.params[0].value == data["params"][0].value
    assert create_task.gameId == data["gameId"]


def test_find_task():
    """
    Test the FindTask model.

    The FindTask model is used for finding a task.

    The model has the following attributes:
    - gameId (UUID): Game ID
    """
    data = {
        "gameId": uuid4()
    }
    find_task = FindTask(**data)
    assert find_task.gameId == data["gameId"]


def test_create_task_post_succesfully_created():
    """
    Test the CreateTaskPostSuccesfullyCreated model.

    The CreateTaskPostSuccesfullyCreated model is used for successful task
    creation response.

    The model has the following attributes:
    - externalTaskId (str): External task ID
    - externalGameId (str): External game ID
    - gameParams (Optional[List[CreateGameParams]]): Game parameters
    - taskParams (Optional[List[CreateTaskParams]]): Task parameters
    - strategy (Optional[Strategy]): Strategy
    """
    data = {
        "message": "Successfully created",
        "externalTaskId": "task123",
        "externalGameId": "game123",
        "gameParams": [CreateGameParams(key="var1", value=10)],
        "taskParams": [CreateTaskParams(key="var2", value=20)],
        "strategy": Strategy(
            id="strategy123",
            version="1.0",
            variables={"var1": 10}
        )
    }
    create_task_post_succesfully_created = CreateTaskPostSuccesfullyCreated(
        **data)
    assert create_task_post_succesfully_created.message == data["message"]
    assert create_task_post_succesfully_created.externalTaskId == (
        data["externalTaskId"]
    )
    assert create_task_post_succesfully_created.externalGameId == (
        data["externalGameId"]
    )
    assert create_task_post_succesfully_created.gameParams == (
        data["gameParams"]
    )
    assert create_task_post_succesfully_created.taskParams == (
        data["taskParams"]
    )
    assert create_task_post_succesfully_created.strategy == data["strategy"]


def test_assigned_points_to_external_user_id():
    """
    Test the AssignedPointsToExternalUserId model.

    The AssignedPointsToExternalUserId model is used for assigning points to an
    external user ID.

    The model has the following attributes:
    - points (int): Points
    - caseName (str): Case name
    - isACreatedUser (bool): Is a created user
    - gameId (UUID): Game ID
    - externalTaskId (str): External task ID
    - created_at (str): Created date
    """
    data = {
        "points": 10,
        "caseName": "Test Case",
        "isACreatedUser": True,
        "gameId": uuid4(),
        "externalTaskId": "task123",
        "created_at": "2023-01-01T00:00:00"
    }
    assigned_points = AssignedPointsToExternalUserId(**data)
    assert assigned_points.points == data["points"]
    assert assigned_points.caseName == data["caseName"]
    assert assigned_points.isACreatedUser == data["isACreatedUser"]
    assert assigned_points.gameId == data["gameId"]
    assert assigned_points.externalTaskId == data["externalTaskId"]
    assert assigned_points.created_at == data["created_at"]


def test_task_points_response_by_user():
    """
    Test the TaskPointsResponseByUser model.

    The TaskPointsResponseByUser model is used for task points response by
      user.

    The model has the following attributes:
    - taskId (str): Task ID
    - externalTaskId (str): External task ID
    - gameId (str): Game ID
    - points (Optional[int]): Points
    """
    data = {
        "taskId": "task123",
        "externalTaskId": "task123",
        "gameId": "game123",
        "points": 100
    }
    task_points_response = TaskPointsResponseByUser(**data)
    assert task_points_response.taskId == data["taskId"]
    assert task_points_response.externalTaskId == data["externalTaskId"]
    assert task_points_response.gameId == data["gameId"]
    assert task_points_response.points == data["points"]


def test_base_user():
    """
    Test the BaseUser model.

    The BaseUser model is used as a base model for a user.

    The model has the following attributes:
    - externalUserId (str): External user ID
    - created_at (Optional[str]): Created date
    """
    data = {
        "externalUserId": "user123",
        "created_at": "2023-01-01T00:00:00"
    }
    base_user = BaseUser(**data)
    assert base_user.externalUserId == data["externalUserId"]
    assert base_user.created_at == data["created_at"]


def test_base_user_first_action():
    """
    Test the BaseUserFirstAction model.

    The BaseUserFirstAction model is used for a user's first action.

    The model has the following attributes:
    - externalUserId (str): External user ID
    - created_at (Optional[str]): Created date
    - firstAction (Optional[str]): First action
    """
    data = {
        "externalUserId": "user123",
        "created_at": "2023-01-01T00:00:00",
        "firstAction": "login"
    }
    user_first_action = BaseUserFirstAction(**data)
    assert user_first_action.externalUserId == data["externalUserId"]
    assert user_first_action.created_at == data["created_at"]
    assert user_first_action.firstAction == data["firstAction"]


def test_tasks_with_users():
    """
    Test the TasksWithUsers model.

    The TasksWithUsers model is used for tasks with users.

    The model has the following attributes:
    - externalTaskId (str): External task ID
    - users (List[BaseUserFirstAction]): List of users
    """
    data = {
        "externalTaskId": "task123",
        "users": [
            BaseUserFirstAction(
                externalUserId="user123",
                created_at="2023-01-01T00:00:00",
                firstAction="login"
            ),
            BaseUserFirstAction(
                externalUserId="user456",
                created_at="2023-01-02T00:00:00",
                firstAction="purchase"
            )
        ]
    }
    tasks_with_users = TasksWithUsers(**data)
    assert tasks_with_users.externalTaskId == data["externalTaskId"]
    assert tasks_with_users.users == data["users"]
