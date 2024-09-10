from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Body
from typing import List
from app.core.container import Container
from app.schema.games_schema import (
    FindGameResult, GameCreated, PatchGame, PostCreateGame, PostFindGame,
    ResponsePatchGame, BaseGameResult, ListTasksWithUsers
)
from app.schema.strategy_schema import Strategy

from app.schema.task_schema import (
    CreateTaskPost, CreateTaskPostSuccesfullyCreated, FoundTasks,
    PostFindTask, AsignPointsToExternalUserId,
    AddActionDidByUserInTask,
    AssignedPointsToExternalUserId
)
from app.schema.user_points_schema import (
    PointsAssignedToUser, AllPointsByGame
)
from app.middlewares.valid_access_token import (
    oauth_2_scheme
)

from app.services.game_service import GameService
from app.services.task_service import TaskService
from app.services.user_points_service import UserPointsService
from uuid import UUID

router = APIRouter(
    prefix="/games",
    tags=["games"],
)

summary_get_games_list = "Retrieve All Games"
description_get_games_list = """
## Retrieve All Games
### This endpoint retrieves a list of all games along with their associated parameters.
<sub>**Id_endpoint:** get_games_list</sub>"""  # noqa


@router.get(
    "",
    response_model=FindGameResult,
    description=description_get_games_list,
    summary=summary_get_games_list,
    dependencies=[Depends(oauth_2_scheme)]
)
@inject
def get_games_list(
    schema: PostFindGame = Depends(),
    service: GameService = Depends(Provide[Container.game_service]),
    token: str = Depends(oauth_2_scheme)
):
    """
  Retrieve a list of all games with their parameters.

   Args:
        schema(PostFindGame): Query parameters for finding games.
        service(GameService): Injected GameService dependency.

    Returns:
        FindGameResult: A result set containing the games and search options.
    """
    return service.get_all_games(schema)


summary_get_game_by_id = "Retrieve Game by ID"
description_get_game_by_id = """
## Retrieve Game by ID
### This endpoint retrieves the details of a game by its unique game ID.
<sub>**Id_endpoint:** get_game_by_id</sub>
"""


@router.get(
    "/{gameId}",
    response_model=BaseGameResult,
    description=description_get_game_by_id,
    summary=summary_get_game_by_id,
)
@inject
def get_game_by_id(
    gameId: UUID,
    service: GameService = Depends(Provide[Container.game_service]),
):
    """
  Retrieve a game by its ID.

   Args:
        gameId(UUID): The ID of the game.
        service(GameService): Injected GameService dependency.

    Returns:
        BaseGameResult: The details of the specified game.
    """
    response = service.get_by_gameId(gameId)
    return response


summary_create_game = "Create a New Game"
description_create_game = """
## Create a New Game
### This endpoint allows for the creation of a new game with the specified parameters.
<sub>**Id_endpoint:** get_game_by_id</sub>"""  # noqa


@router.post(
    "",
    response_model=GameCreated,
    summary=summary_create_game,
    description=description_create_game,
)
@inject
def create_game(
    schema: PostCreateGame = Body(..., example=PostCreateGame.example()),
    service: GameService = Depends(Provide[Container.game_service]),
):
    """
    Create a new game.

    Args:
        schema (PostCreateGame): The schema for creating a new game.
        service (GameService): Injected GameService dependency.

    Returns:
        GameCreated: The details of the created game.
    """
    return service.create(schema)


summary_patch_game = "Update Game Details"
description_patch_game = """
## Update Game Details
### This endpoint allows for updating the details of a game by its ID, including game parameters. 
<sub>**Id_endpoint:** patch_game"""  # noqa


@router.patch(
    "/{gameId}",
    response_model=ResponsePatchGame,
    summary=summary_patch_game,
    description=description_patch_game,
)
@inject
def patch_game(
    gameId: UUID,
    schema: PatchGame,
    service: GameService = Depends(Provide[Container.game_service]),
):
    """
    Update a game by its ID.

    Args:
        gameId (UUID): The ID of the game to update.
        schema (PatchGame): The schema for updating the game.
        service (GameService): Injected GameService dependency.

    Returns:
        ResponsePatchGame: The updated game details.
    """
    return service.patch_game_by_id(gameId, schema)


summary_get_strategy_by_gameId = "Retrieve Strategy by Game ID"
description_get_strategy_by_gameId = """
## Retrieve Strategy by Game ID
### This endpoint retrieves the strategy details associated with a specific game by its ID.
<sub>**Id_endpoint:** get_strategy_by_gameId</sub>"""  # noqa


@router.get(
    "/{gameId}/strategy",
    response_model=Strategy,
    summary=summary_get_strategy_by_gameId,
    description=description_get_strategy_by_gameId,
)
@inject
def get_strategy_by_gameId(
    gameId: UUID,
    service: GameService = Depends(Provide[Container.game_service]),
):
    """
    Retrieve the strategy associated with a game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (GameService): Injected GameService dependency.

    Returns:
        Strategy: The strategy associated with the specified game.
    """
    return service.get_strategy_by_gameId(gameId)


summary_create_task = "Create a New Task"
description_create_task = """
## Create a New Task
### This endpoint allows for the creation of a new task within a specific game using the game's ID. 
<sub>**Id_endpoint:** create_task</sub>"""  # noqa


@router.post(
    "/{gameId}/tasks",
    response_model=CreateTaskPostSuccesfullyCreated,
    summary=summary_create_task,
    description=description_create_task,
)
@inject
def create_task(
    gameId: UUID,
    create_query: CreateTaskPost = Body(..., example=CreateTaskPost.example()),
    service: TaskService = Depends(Provide[Container.task_service]),

):
    """
    Create a task for a specific game.

    Args:
        gameId (UUID): The ID of the game.
        create_query (CreateTaskPost): The schema for creating a task.
        service (TaskService): Injected TaskService dependency.

    Returns:
        CreateTaskPostSuccesfullyCreated: The details of the created task.
    """
    return service.create_task_by_game_id(gameId, create_query)


summary_get_task_list = "Retrieve Task List"
description_get_task_list = """
## Retrieve Task List
### This endpoint retrieves a list of tasks associated with a specific game using the game's ID. 
<sub>**Id_endpoint:** get_task_list</sub>"""  # noqa


@router.get(
    "/{gameId}/tasks",
    response_model=FoundTasks,
    summary=summary_get_task_list,
    description=description_get_task_list,
)
@inject
def get_task_list(
    gameId: UUID,
    find_query: PostFindTask = Depends(),
    service: TaskService = Depends(Provide[Container.task_service]),
):
    """
    Retrieve a list of tasks for a specific game.

    Args:
        gameId (UUID): The ID of the game.
        find_query (PostFindTask): Query parameters for finding tasks.
        service (TaskService): Injected TaskService dependency.

    Returns:
        FoundTasks: A result set containing the tasks.
    """
    return service.get_tasks_list_by_gameId(gameId, find_query)


summary_get_task_by_gameId_taskId = (
    "Retrieve Task by Game ID and External Task ID"
)
description_get_task_by_gameId_taskId = """
## Retrieve Task by Game ID and External Task ID
### This endpoint retrieves the details of a task using the game's ID and the external task ID. 
<sub>**Id_endpoint:** get_task_by_gameId_taskId</sub>"""  # noqa


@router.get(
    "/{gameId}/tasks/{externalTaskId}",
    response_model=CreateTaskPostSuccesfullyCreated,
    summary=summary_get_task_by_gameId_taskId,
    description=description_get_task_by_gameId_taskId,
)
@inject
def get_task_by_gameId_taskId(
    gameId: UUID,
    externalTaskId: str,
    service: TaskService = Depends(Provide[Container.task_service]),
):
    """
    Retrieve a task by its external game ID and external task ID.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        service (TaskService): Injected TaskService dependency.

    Returns:
        CreateTaskPostSuccesfullyCreated: The details of the specified task.
    """
    return service.get_task_by_externalGameId_externalTaskId(
        str(gameId), externalTaskId)


summary_get_points_by_gameId = "Retrieve Points by Game ID"
description_get_points_by_gameId = """
## Retrieve Points by Game ID
### This endpoint retrieves the points details associated with a specific game by its ID. 
<sub>**Id_endpoint:** get_points_by_gameId</sub>"""  # noqa


@router.get(
    "/{gameId}/points",
    response_model=AllPointsByGame,
    summary=summary_get_points_by_gameId,
    description=description_get_points_by_gameId,
)
@inject
def get_points_by_gameId(
    gameId: UUID,
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    """
    Retrieve points associated with a specific game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (UserPointsService): Injected UserPointsService dependency.

    Returns:
        AllPointsByGame: The points details for the specified game.
    """
    return service.get_points_by_gameId(gameId)


summary_get_points_of_user_in_game = "Retrieve User Points in Game"
description_get_points_of_user_in_game = """
## Retrieve User Points in Game
### This endpoint retrieves the points details of a user within a specific game using the game's ID and the user's external ID. 
<sub>**Id_endpoint:** get_points_of_user_in_game</sub>
"""  # noqa


@router.get(
    "/{gameId}/users/{externalUserId}/points",
    response_model=List[PointsAssignedToUser],
    summary=summary_get_points_of_user_in_game,
    description=description_get_points_of_user_in_game,
)
@inject
def get_points_of_user_in_game(
    gameId: UUID,
    externalUserId: str,
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    """
    Retrieve points of a user in a specific game.

    Args:
        gameId (UUID): The ID of the game.
        externalUserId (str): The external user ID.
        service (UserPointsService): Injected UserPointsService dependency.

    Returns:
        List[PointsAssignedToUser]: The points details of the user in the
          specified game.
    """
    return service.get_points_of_user_in_game(gameId, externalUserId)


summary_user_action = "User Action"
description_user_action = """
## User Action
### This endpoint allows for the assignment of points to a user for a specific task within a game.
<sub>**Id_endpoint:** user_action_in_task</sub>
"""  # noqa


@router.post(
    "/{gameId}/tasks/{externalTaskId}/action",
    response_model=AddActionDidByUserInTask,
    summary=summary_user_action,
    description=description_user_action,
)
@inject
def user_action_in_task(
    gameId: UUID,
    externalTaskId: str,
    schema: AddActionDidByUserInTask = Body(...),
    service: TaskService = Depends(Provide[Container.task_service]),
):
    """
    Register a user action in a task within a game. This endpoint is used to
    assign points to a user for a specific task within a game, when the game
    requires it.
    """
    return service.user_add_action_in_task(gameId, externalTaskId, schema)


summary_assing_points_to_user = "Assign Points to User"
description_assing_points_to_user = """
## Assign Points to User
### This endpoint assigns points to a user for a specific task within a game. 
<sub>**Id_endpoint:** assign_points_to_user</sub>
"""  # noqa


@ router.post(
    "/{gameId}/tasks/{externalTaskId}/points",
    response_model=AssignedPointsToExternalUserId,
    summary=summary_assing_points_to_user,
    description=description_assing_points_to_user,
)
@ inject
def assign_points_to_user(
    gameId: UUID,
    externalTaskId: str,
    schema: AsignPointsToExternalUserId = Body(...),
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    """
    Assign points to a user for a specific task in a game.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        schema (AsignPointsToExternalUserId): The schema for assigning points.
        service (UserPointsService): Injected UserPointsService dependency.

    Returns:
        AssignedPointsToExternalUserId: The details of the points assigned.
    """
    return service.assign_points_to_user(gameId, externalTaskId, schema)


summary_get_points_by_task_id = "Retrieve Points by Task ID"
description_get_points_by_task_id = """
## Retrieve Points by Task ID
### This endpoint retrieves the points details associated with a specific task using the game's ID and the external task ID. 
<sub>**Id_endpoint:** get_points_by_task_id</sub>"""  # noqa


@ router.get(
    "/{gameId}/tasks/{externalTaskId}/points",
    response_model=List[PointsAssignedToUser],
    summary=summary_get_points_by_task_id,
    description=description_get_points_by_task_id,
)
@ inject
def get_points_by_task_id(
    gameId: UUID,
    externalTaskId: str,
    service: TaskService = Depends(Provide[Container.task_service]),
):
    """
    Retrieve points by task ID.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        service (TaskService): Injected TaskService dependency.

    Returns:
        List[PointsAssignedToUser]: The points details for the specified task.
    """
    return service.get_points_by_task_id(gameId, externalTaskId)


summary_get_points_of_user_by_task_id = "Retrieve User Points by Task ID"
description_get_points_of_user_by_task_id = """
## Retrieve User Points by Task ID
### This endpoint retrieves the points details of a user associated with a specific task using the game's ID and the user's external ID. 
<sub>**Id_endpoint:** get_points_of_user_by_task_id</sub>"""  # noqa


@ router.get(
    "/{gameId}/tasks/{externalTaskId}/users/{externalUserId}/points",
    response_model=PointsAssignedToUser,
    summary=summary_get_points_of_user_by_task_id,
    description=description_get_points_of_user_by_task_id,
)
@ inject
def get_points_of_user_by_task_id(
    gameId: UUID,
    externalTaskId: str,
    externalUserId: str,
    service: TaskService = Depends(Provide[Container.task_service])
):
    """
    Retrieve points of a user by task ID.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        externalUserId (str): The external user ID.
        service (TaskService): Injected TaskService dependency.

    Returns:
        PointsAssignedToUser: The points details of the user for the specified
          task.
    """
    return service.get_points_of_user_by_task_id(
        gameId,
        externalTaskId,
        externalUserId
    )


summary_get_points_by_task_id_with_details = (
    "Retrieve Detailed Points by Task ID"
)
description_get_points_by_task_id_with_details = """
## Retrieve Detailed Points by Task ID
### This endpoint retrieves detailed points information associated with a specific task using the game's ID and the external task ID. 
<sub>**Id_endpoint:** get_points_by_task_id_with_details</sub>
"""  # noqa


@ router.get(
    "/{gameId}/tasks/{externalTaskId}/points/details",
    response_model=List[dict],  # WIP FIX
    summary=summary_get_points_by_task_id_with_details,
    description=description_get_points_by_task_id_with_details,
)
@ inject
def get_points_by_task_id_with_details(
    gameId: UUID,
    externalTaskId: str,
    service: TaskService = Depends(Provide[Container.task_service]),
):
    """
    Retrieve detailed points by task ID.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        service (TaskService): Injected TaskService dependency.

    Returns:
        List[dict]: Detailed points information for the specified task.
    """
    return service.get_points_by_task_id_with_details(gameId, externalTaskId)


summary_get_users_by_gameId = "Retrieve Users by Game ID"
description_get_users_by_gameId = """
## Retrieve Users by Game ID
### This endpoint retrieves the list of users associated with a specific game using the game's ID. 
<sub>**Id_endpoint:** get_users_by_gameId</sub>
"""  # noqa


@ router.get(
    "/{gameId}/users",
    response_model=ListTasksWithUsers,
    summary=summary_get_users_by_gameId,
    description=description_get_users_by_gameId,
)
@ inject
def get_users_by_gameId(
    gameId: UUID,
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    """
    Retrieve users associated with a game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (UserPointsService): Injected UserPointsService dependency.

    Returns:
        ListTasksWithUsers: The list of users associated with the specified
          game.
    """
    return service.get_users_by_gameId(gameId)
