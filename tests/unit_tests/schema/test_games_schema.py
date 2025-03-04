from datetime import datetime
from uuid import uuid4

from app.schema.base_schema import SearchOptions
from app.schema.games_params_schema import (BaseFindGameParams, CreateGameParams,
                                            UpdateGameParams)
from app.schema.games_schema import (BaseGame, BaseGameResult, FindGameById,
                                     FindGameResult, GameCreated, ListTasksWithUsers,
                                     PatchGame, PostCreateGame, PostFindGame,
                                     ResponsePatchGame)
from app.schema.task_schema import TasksWithUsers


def test_base_game():
    """
    Test the BaseGame model.

    The BaseGame model is used as a base model for a game.

    The model has the following attributes:
    - platform (str): Platform name
    """
    data = {"platform": "PC"}
    game = BaseGame(**data)
    assert game.platform == data["platform"]


def test_base_game_result():
    """
    Test the BaseGameResult model.

    The BaseGameResult model is used for game results.

    The model has the following attributes:
    - gameId (UUID): Game ID
    - created_at (Optional[datetime]): Created date
    - updated_at (Optional[datetime]): Updated date
    - externalGameId (Optional[str]): External game ID
    - strategyId (Optional[str]): Strategy ID
    - platform (Optional[str]): Platform name
    - params (Optional[List[BaseFindGameParams]]): Game parameters
    """
    data = {
        "gameId": uuid4(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "externalGameId": "external123",
        "strategyId": "strategy123",
        "platform": "PC",
        "params": [BaseFindGameParams(id=uuid4(), key="difficulty", value="hard")],
    }
    result = BaseGameResult(**data)
    assert result.gameId == data["gameId"]
    assert result.created_at == data["created_at"]
    assert result.updated_at == data["updated_at"]
    assert result.externalGameId == data["externalGameId"]
    assert result.strategyId == data["strategyId"]
    assert result.platform == data["platform"]
    assert result.params == data["params"]


def test_post_create_game():
    """
    Test the PostCreateGame model.

    The PostCreateGame model is used for creating a game.

    The model has the following attributes:
    - externalGameId (str): External game ID
    - platform (str): Platform name
    - strategyId (Optional[str]): Strategy ID
    - params (Optional[List[CreateGameParams]]): Game parameters
    """
    data = {
        "externalGameId": "external123",
        "platform": "PC",
        "strategyId": "strategy123",
        "params": [CreateGameParams(key="difficulty", value="hard")],
    }
    game = PostCreateGame(**data)
    assert game.externalGameId == data["externalGameId"]
    assert game.platform == data["platform"]
    assert game.strategyId == data["strategyId"]
    assert game.params == data["params"]


def test_patch_game():
    """
    Test the PatchGame model.

    The PatchGame model is used for updating a game.

    The model has the following attributes:
    - externalGameId (Optional[str]): External game ID
    - strategyId (Optional[str]): Strategy ID
    - platform (Optional[str]): Platform name
    - params (Optional[List[UpdateGameParams]]): Game parameters
    """
    data = {
        "externalGameId": "external123",
        "strategyId": "strategy123",
        "platform": "PC",
        "params": [UpdateGameParams(id=uuid4(), key="difficulty", value="hard")],
    }
    game = PatchGame(**data)
    assert game.externalGameId == data["externalGameId"]
    assert game.strategyId == data["strategyId"]
    assert game.platform == data["platform"]
    assert game.params == data["params"]


def test_game_created():
    """
    Test the GameCreated model.

    The GameCreated model is used for game creation response.

    The model has the following attributes:
    - message (Optional[str]): Success message
    """
    data = {
        "gameId": uuid4(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "externalGameId": "external123",
        "strategyId": "strategy123",
        "platform": "PC",
        "params": [BaseFindGameParams(id=uuid4(), key="difficulty", value="hard")],
        "message": "Game successfully created",
    }
    game = GameCreated(**data)
    assert game.message == data["message"]


def test_response_patch_game():
    """
    Test the ResponsePatchGame model.

    The ResponsePatchGame model is used for game update response.

    The model has the following attributes:
    - message (Optional[str]): Success message
    """
    data = {
        "externalGameId": "external123",
        "strategyId": "strategy123",
        "platform": "PC",
        "params": [UpdateGameParams(id=uuid4(), key="difficulty", value="hard")],
        "message": "Game successfully updated",
    }
    game = ResponsePatchGame(**data)
    assert game.message == data["message"]


def test_find_game_by_id():
    """
    Test the FindGameById model.

    The FindGameById model is used for finding a game by ID.

    The model has the following attributes:
    - externalGameId (Optional[str]): External game ID
    - platform (Optional[str]): Platform name
    - params (Optional[List[UpdateGameParams]]): Game parameters
    """
    data = {
        "id": uuid4(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "externalGameId": "external123",
        "platform": "PC",
        "params": [UpdateGameParams(id=uuid4(), key="difficulty", value="hard")],
    }
    game = FindGameById(**data)
    assert game.externalGameId == data["externalGameId"]
    assert game.platform == data["platform"]
    assert game.params == data["params"]


def test_post_find_game():
    """
    Test the PostFindGame model.

    The PostFindGame model is used for finding a game.

    The model inherits attributes from FindBase and BaseGame.
    """
    data = {"ordering": "asc", "page": 1, "page_size": 10, "platform": "PC"}
    game = PostFindGame(**data)
    assert game.ordering == data["ordering"]
    assert game.page == data["page"]
    assert game.page_size == data["page_size"]
    assert game.platform == data["platform"]


def test_find_game_result():
    """
    Test the FindGameResult model.

    The FindGameResult model is used for game search results.

    The model has the following attributes:
    - items (Optional[List[BaseGameResult]]): List of game results
    - search_options (Optional[SearchOptions]): Search options
    """
    data = {
        "items": [
            BaseGameResult(
                gameId=uuid4(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                externalGameId="external123",
                strategyId="strategy123",
                platform="PC",
                params=[BaseFindGameParams(id=uuid4(), key="difficulty", value="hard")],
            )
        ],
        "search_options": SearchOptions(
            ordering="asc", page=1, page_size=10, total_count=1
        ),
    }
    result = FindGameResult(**data)
    assert result.items == data["items"]
    assert result.search_options == data["search_options"]


def test_list_tasks_with_users():
    """
    Test the ListTasksWithUsers model.

    The ListTasksWithUsers model is used for listing tasks with users.

    The model has the following attributes:
    - gameId (UUID): Game ID
    - tasks (List[TasksWithUsers]): List of tasks with users
    """
    data = {
        "gameId": uuid4(),
        "tasks": [
            TasksWithUsers(
                externalTaskId=str(uuid4()),
                taskName="Test Task",
                users=[
                    {"externalUserId": str(uuid4()), "points": 10},
                    {"externalUserId": str(uuid4()), "points": 20},
                ],
            )
        ],
    }
    tasks_with_users = ListTasksWithUsers(**data)
    assert tasks_with_users.gameId == data["gameId"]
    assert tasks_with_users.tasks == data["tasks"]
