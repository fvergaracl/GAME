from datetime import datetime
from uuid import uuid4

from app.schema.user_points_schema import (AllPointsByGame, GameDetail,
                                           PointsAssigned,
                                           PointsAssignedToUser,
                                           PointsByUserInTask, PointsData,
                                           PointsDetail,
                                           PostAssignPointsToUser,
                                           ResponseGetPointsByGame,
                                           ResponseGetPointsByTask,
                                           ResponsePointsByExternalUserId,
                                           TaskDetail, TaskPointsByGame,
                                           UserGamePoints, UserPoints,
                                           UserPointsAssign,
                                           UserPointsAssigned)
from app.schema.wallet_schema import WalletWithoutUserId


def test_post_assign_points_to_user():
    """
    Test the PostAssignPointsToUser model.

    The PostAssignPointsToUser model is used for assigning points to a user.

    The model has the following attributes:
    - taskId (str): Task ID
    - caseName (Optional[str]): Case name
    - points (Optional[int]): Points
    - description (Optional[str]): Description
    - data (Optional[dict]): Additional data
    """
    data = {
        "taskId": "task123",
        "caseName": "Case1",
        "points": 10,
        "description": "Test description",
        "data": {"key": "value"},
    }
    assign_points = PostAssignPointsToUser(**data)
    assert assign_points.taskId == data["taskId"]
    assert assign_points.caseName == data["caseName"]
    assert assign_points.points == data["points"]
    assert assign_points.description == data["description"]
    assert assign_points.data == data["data"]


def test_points_assigned():
    """
    Test the PointsAssigned model.

    The PointsAssigned model is used for assigned points.

    The model has the following attributes:
    - points (int): Points
    - timesAwarded (int): Times awarded
    """
    data = {"points": 100, "timesAwarded": 5}
    points_assigned = PointsAssigned(**data)
    assert points_assigned.points == data["points"]
    assert points_assigned.timesAwarded == data["timesAwarded"]


def test_points_data():
    """
    Test the PointsData model.

    The PointsData model is used for points data.

    The model has the following attributes:
    - points (int): Points
    - caseName (str): Case name
    - created_at (str): Created date
    """
    data = {"points": 50, "caseName": "Case2", "created_at": "2023-01-01T00:00:00"}
    points_data = PointsData(**data)
    assert points_data.points == data["points"]
    assert points_data.caseName == data["caseName"]
    assert points_data.created_at == data["created_at"]


def test_points_assigned_to_user():
    """
    Test the PointsAssignedToUser model.

    The PointsAssignedToUser model is used for points assigned to a user.

    The model has the following attributes:
    - externalUserId (str): External user ID
    - pointsData (Optional[List[PointsData]]): Points data
    """
    data = {
        "externalUserId": "user123",
        "points": 100,
        "timesAwarded": 3,
        "pointsData": [
            {"points": 50, "caseName": "Case2", "created_at": "2023-01-01T00:00:00"}
        ],
    }
    points_assigned_to_user = PointsAssignedToUser(**data)
    assert points_assigned_to_user.externalUserId == data["externalUserId"]
    assert points_assigned_to_user.pointsData[0].points == (
        data["pointsData"][0]["points"]
    )
    assert points_assigned_to_user.pointsData[0].caseName == (
        data["pointsData"][0]["caseName"]
    )
    assert points_assigned_to_user.pointsData[0].created_at == (
        data["pointsData"][0]["created_at"]
    )


def test_task_points_by_game():
    """
    Test the TaskPointsByGame model.

    The TaskPointsByGame model is used for task points by game.

    The model has the following attributes:
    - externalTaskId (str): External task ID
    - points (List[PointsAssignedToUser]): Points assigned to user
    """
    data = {
        "externalTaskId": "task123",
        "points": [
            {
                "externalUserId": "user123",
                "points": 100,  # Añadir el campo faltante
                "timesAwarded": 1,  # Añadir el campo faltante
                "pointsData": [
                    {
                        "points": 100,
                        "caseName": "Case1",
                        "created_at": "2023-01-01T00:00:00",
                    }
                ],
            }
        ],
    }
    task_points_by_game = TaskPointsByGame(**data)
    assert task_points_by_game.externalTaskId == data["externalTaskId"]
    assert task_points_by_game.points[0].externalUserId == (
        data["points"][0]["externalUserId"]
    )
    assert task_points_by_game.points[0].points == data["points"][0]["points"]
    assert task_points_by_game.points[0].timesAwarded == (
        data["points"][0]["timesAwarded"]
    )
    assert task_points_by_game.points[0].pointsData[0].points == (
        data["points"][0]["pointsData"][0]["points"]
    )
    assert task_points_by_game.points[0].pointsData[0].caseName == (
        data["points"][0]["pointsData"][0]["caseName"]
    )
    assert task_points_by_game.points[0].pointsData[0].created_at == (
        data["points"][0]["pointsData"][0]["created_at"]
    )


def test_all_points_by_game():
    """
    Test the AllPointsByGame model.

    The AllPointsByGame model is used for all points by game.

    The model has the following attributes:
    - externalGameId (str): External game ID
    - created_at (str): Created date
    - task (List[TaskPointsByGame]): List of task points by game
    """
    data = {
        "externalGameId": "game123",
        "created_at": "2023-01-01T00:00:00",
        "task": [
            {
                "externalTaskId": "task123",
                "points": [
                    {
                        "externalUserId": "user123",
                        "points": 50,  # Añadir el campo faltante
                        "timesAwarded": 1,  # Añadir el campo faltante
                        "pointsData": [
                            {
                                "points": 50,
                                "caseName": "Case2",
                                "created_at": "2023-01-01T00:00:00",
                            }
                        ],
                    }
                ],
            }
        ],
    }
    all_points_by_game = AllPointsByGame(**data)
    assert all_points_by_game.externalGameId == data["externalGameId"]
    assert all_points_by_game.created_at == data["created_at"]
    assert all_points_by_game.task[0].externalTaskId == (
        data["task"][0]["externalTaskId"]
    )
    assert all_points_by_game.task[0].points[0].externalUserId == (
        data["task"][0]["points"][0]["externalUserId"]
    )
    assert all_points_by_game.task[0].points[0].points == (
        data["task"][0]["points"][0]["points"]
    )
    assert all_points_by_game.task[0].points[0].timesAwarded == (
        data["task"][0]["points"][0]["timesAwarded"]
    )
    assert all_points_by_game.task[0].points[0].pointsData[0].points == (
        data["task"][0]["points"][0]["pointsData"][0]["points"]
    )
    assert (
        all_points_by_game.task[0].points[0].pointsData[0].caseName
        == data["task"][0]["points"][0]["pointsData"][0]["caseName"]
    )
    assert all_points_by_game.task[0].points[0].pointsData[0].created_at == (
        data["task"][0]["points"][0]["pointsData"][0]["created_at"]
    )


def test_user_points_assign():
    """
    Test the UserPointsAssign model.

    The UserPointsAssign model is used for user points assignment.
    """
    data = {
        "userId": "user123",
        "taskId": "task123",
        "caseName": "Case1",
        "points": 10,
        "description": "Test description",
        "data": {"key": "value"},
    }
    user_points_assign = UserPointsAssign(**data)
    assert user_points_assign.userId == data["userId"]
    assert user_points_assign.taskId == data["taskId"]
    assert user_points_assign.caseName == data["caseName"]
    assert user_points_assign.points == data["points"]
    assert user_points_assign.description == data["description"]
    assert user_points_assign.data == data["data"]


def test_user_points_assigned():
    """
    Test the UserPointsAssigned model.

    The UserPointsAssigned model is used for user points assignment response.

    The model has the following attributes:
    - userId (str): User ID
    - taskId (str): Task ID
    - wallet (Optional[WalletWithoutUserId]): Wallet
    - description (Optional[str]): Description
    - message (Optional[str]): Success message
    """
    wallet_data = {"coinsBalance": 100.0, "pointsBalance": 200.0, "conversionRate": 1.5}

    wallet = WalletWithoutUserId(**wallet_data)

    data = {
        "id": uuid4(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "userId": "user123",
        "taskId": "task123",
        "wallet": wallet,
        "description": "Points assigned successfully",
        "message": "Successfully assigned",
    }
    user_points_assigned = UserPointsAssigned(**data)
    assert user_points_assigned.userId == data["userId"]
    assert user_points_assigned.taskId == data["taskId"]
    assert user_points_assigned.wallet == wallet
    assert user_points_assigned.wallet.coinsBalance == (wallet_data["coinsBalance"])
    assert user_points_assigned.wallet.pointsBalance == (wallet_data["pointsBalance"])
    assert user_points_assigned.wallet.conversionRate == (wallet_data["conversionRate"])
    assert user_points_assigned.description == data["description"]
    assert user_points_assigned.message == data["message"]


def test_user_points():
    """
    Test the UserPoints model.

    The UserPoints model is used for user points.
    """
    data = {
        "id": uuid4(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "userId": "user123",
        "taskId": "task123",
        "caseName": "Case1",
        "points": 10,
        "description": "Test description",
        "data": {"key": "value"},
    }
    user_points = UserPoints(**data)
    assert user_points.userId == data["userId"]
    assert user_points.taskId == data["taskId"]
    assert user_points.caseName == data["caseName"]
    assert user_points.points == data["points"]
    assert user_points.description == data["description"]
    assert user_points.data == data["data"]


def test_response_get_points_by_task():
    """
    Test the ResponseGetPointsByTask model.

    The ResponseGetPointsByTask model is used for points by task response.

    The model has the following attributes:
    - externalUserId (str): External user ID
    - points (int): Points
    """
    data = {"externalUserId": "user123", "points": 100}
    response = ResponseGetPointsByTask(**data)
    assert response.externalUserId == data["externalUserId"]
    assert response.points == data["points"]


def test_points_detail():
    """
    Test the PointsDetail model.

    The PointsDetail model is used for points detail.

    The model has the following attributes:
    - points (int): Points
    - caseName (str): Case name
    - created_at (str): Created date
    """
    data = {"points": 100, "caseName": "Case1", "created_at": "2023-01-01T00:00:00"}
    points_detail = PointsDetail(**data)
    assert points_detail.points == data["points"]
    assert points_detail.caseName == data["caseName"]
    assert points_detail.created_at == data["created_at"]


def test_task_detail():
    """
    Test the TaskDetail model.

    The TaskDetail model is used for task detail.

    The model has the following attributes:
    - externalTaskId (str): External task ID
    - pointsData (List[PointsDetail]): Points data
    """
    data = {
        "externalTaskId": "task123",
        "pointsData": [
            {"points": 100, "caseName": "Case1", "created_at": "2023-01-01T00:00:00"}
        ],
    }
    task_detail = TaskDetail(**data)
    assert task_detail.externalTaskId == data["externalTaskId"]
    assert task_detail.pointsData[0].points == data["pointsData"][0]["points"]


def test_game_detail():
    """
    Test the GameDetail model.

    The GameDetail model is used for game detail.

    The model has the following attributes:
    - externalGameId (str): External game ID
    - points (int): Points
    - timesAwarded (int): Times awarded
    - tasks (List[TaskDetail]): List of task details
    """
    data = {
        "externalGameId": "game123",
        "points": 100,
        "timesAwarded": 5,
        "tasks": [
            {
                "externalTaskId": "task123",
                "pointsData": [
                    {
                        "points": 100,
                        "caseName": "Case1",
                        "created_at": "2023-01-01T00:00:00",
                    }
                ],
            }
        ],
    }
    game_detail = GameDetail(**data)
    assert game_detail.externalGameId == data["externalGameId"]
    assert game_detail.points == data["points"]
    assert game_detail.timesAwarded == data["timesAwarded"]
    assert game_detail.tasks[0].externalTaskId == (data["tasks"][0]["externalTaskId"])


def test_user_game_points():
    """
    Test the UserGamePoints model.

    The UserGamePoints model is used for user game points.

    The model has the following attributes:
    - externalUserId (str): External user ID
    - points (int): Points
    - timesAwarded (int): Times awarded
    - games (List[GameDetail]): List of game details
    - userExists (Optional[bool]): If the user exists
    """
    data = {
        "externalUserId": "user123",
        "points": 100,
        "timesAwarded": 5,
        "games": [
            {
                "externalGameId": "game123",
                "points": 100,
                "timesAwarded": 5,
                "tasks": [
                    {
                        "externalTaskId": "task123",
                        "pointsData": [
                            {
                                "points": 100,
                                "caseName": "Case1",
                                "created_at": "2023-01-01T00:00:00",
                            }
                        ],
                    }
                ],
            }
        ],
        "userExists": True,
    }
    user_game_points = UserGamePoints(**data)
    assert user_game_points.externalUserId == data["externalUserId"]
    assert user_game_points.points == data["points"]
    assert user_game_points.timesAwarded == data["timesAwarded"]
    assert user_game_points.games[0].externalGameId == (
        data["games"][0]["externalGameId"]
    )
    assert user_game_points.userExists == data["userExists"]


def test_response_get_points_by_game():
    """
    Test the ResponseGetPointsByGame model.

    The ResponseGetPointsByGame model is used for points by game response.

    The model has the following attributes:
    - externalTaskId (str): External task ID
    - points (List[ResponseGetPointsByTask]): Points by task
    """
    data = {
        "externalTaskId": "task123",
        "points": [{"externalUserId": "user123", "points": 100}],
    }
    response = ResponseGetPointsByGame(**data)
    assert response.externalTaskId == data["externalTaskId"]
    assert response.points[0].externalUserId == (data["points"][0]["externalUserId"])
    assert response.points[0].points == data["points"][0]["points"]


def test_points_by_user_in_task():
    """
    Test the PointsByUserInTask model.

    The PointsByUserInTask model is used for points by user in task.

    The model has the following attributes:
    - externalTaskId (str): External task ID
    - points (int): Points
    """
    data = {"externalTaskId": "task123", "points": 100}
    points_by_user_in_task = PointsByUserInTask(**data)
    assert points_by_user_in_task.externalTaskId == data["externalTaskId"]
    assert points_by_user_in_task.points == data["points"]


def test_response_points_by_external_user_id():
    """
    Test the ResponsePointsByExternalUserId model.

    The ResponsePointsByExternalUserId model is used for points by external
      user ID response.

    The model has the following attributes:
    - externalUserId (str): External user ID
    - points (int): Points
    - points_by_task (List[PointsByUserInTask]): Points by task
    """
    data = {
        "externalUserId": "user123",
        "points": 100,
        "points_by_task": [{"externalTaskId": "task123", "points": 100}],
    }
    response = ResponsePointsByExternalUserId(**data)
    assert response.externalUserId == data["externalUserId"]
    assert response.points == data["points"]
    assert response.points_by_task[0].externalTaskId == (
        data["points_by_task"][0]["externalTaskId"]
    )
    assert response.points_by_task[0].points == (data["points_by_task"][0]["points"])
