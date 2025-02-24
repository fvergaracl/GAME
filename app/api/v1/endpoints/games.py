from typing import List
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends

from app.core.container import Container
from app.schema.games_schema import (
    BaseGameResult,
    FindGameResult,
    GameCreated,
    ListTasksWithUsers,
    PatchGame,
    PostCreateGame,
    PostFindGame,
    ResponsePatchGame,
)
from app.schema.strategy_schema import Strategy
from app.schema.task_schema import (
    AddActionDidByUserInTask,
    AsignPointsToExternalUserId,
    AssignedPointsToExternalUserId,
    CreateTaskPost,
    CreateTaskPostSuccesfullyCreated,
    CreateTasksPostBulkCreated,
    FoundTasks,
    PostFindTask,
    CreateTasksPost,
    ResponseAddActionDidByUserInTask,
    SimulatedPointsAssignedToUser,
)
from app.schema.user_points_schema import (
    AllPointsByGame,
    AllPointsByGameWithDetails,
    PointsAssignedToUser,
)
from app.services.apikey_service import ApiKeyService
from app.services.game_service import GameService
from app.services.logs_service import LogsService
from app.services.task_service import TaskService
from app.services.oauth_users_service import OAuthUsersService
from app.schema.oauth_users_schema import CreateOAuthUser
from app.services.user_actions_service import UserActionsService
from app.services.user_points_service import UserPointsService
from app.middlewares.authentication import auth_api_key_or_oauth2
from app.middlewares.valid_access_token import oauth_2_scheme, valid_access_token
from app.util.check_role import check_role
from app.util.add_log import add_log

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
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_games_list(
    schema: PostFindGame = Depends(),
    service: GameService = Depends(Provide[Container.game_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve a list of all games with their parameters.

    Args:
        schema(PostFindGame): Query parameters for finding games.
        service(GameService): Injected GameService dependency.
        service_log(LogsService): Injected LogsService dependency.
        service_oauth(OAuthUsersService): Injected OAuthUsersService dependency.
        token(str): The OAuth2 token.
        api_key_header(str): The API key header.


    Returns:
        FindGameResult: A result set containing the games and search options.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Get games list - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
        is_admin = check_role(token_data, "AdministratorGAME")
        if is_admin:
            return service.get_all_games(schema)
    await add_log(
        "game",
        "INFO",
        "Game list retrieval",
        schema.dict(),
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_all_games(schema, api_key)


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
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_game_by_id(
    gameId: UUID,
    service: GameService = Depends(Provide[Container.game_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve a game by its ID.

    Args:
        gameId(UUID): The ID of the game.
        service(GameService): Injected GameService dependency.
        service_log(LogsService): Injected LogsService dependency.
        service_oauth(OAuthUsersService): Injected OAuthUsersService dependency.
        token(str): The OAuth2 token.
        api_key_header(str): The API key header.

    Returns:
        BaseGameResult: The details of the specified game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Get game by ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Game retrieval by ID",
        {"gameId": str(gameId)},
        service_log,
        api_key,
        oauth_user_id,
    )
    response = service.get_by_gameId(gameId)
    return response


# delete game by gameId
summary_delete_game_by_id = "Delete Game by ID"
description_delete_game_by_id = """
## Delete Game by ID
### This endpoint deletes a game by its unique game ID.
<sub>**Id_endpoint:** delete_game_by_id</sub>"""  # noqa


@router.delete(
    "/{gameId}",
    response_model=BaseGameResult,
    description=description_delete_game_by_id,
    summary=summary_delete_game_by_id,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def delete_game_by_id(
    gameId: UUID,
    service: GameService = Depends(Provide[Container.game_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Delete a game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (GameService): Injected GameService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        BaseGameResult: The details of the deleted game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Delete game by ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )

    await add_log(
        "game",
        "INFO",
        "Game deletion by ID",
        {"gameId": str(gameId)},
        service_log,
        api_key,
        oauth_user_id,
    )

    try:
        response = service.delete_game_by_id(gameId)
        data_to_log = {"gameId": str(gameId)}
        await add_log(
            "game",
            "SUCCESS",
            "Game deletion successful",
            data_to_log,
            service_log,
            api_key,
            oauth_user_id,
        )
        return response
    except Exception as e:
        await add_log(
            "game",
            "ERROR",
            "Game deletion failed",
            {"error": str(e)},
            service_log,
            api_key,
            oauth_user_id,
        )
        raise e


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
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def create_game(
    schema: PostCreateGame = Body(..., example=PostCreateGame.example()),
    service: GameService = Depends(Provide[Container.game_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Create a new game.

    Args:
        schema (PostCreateGame): The schema for creating a new game.
        service (GameService): Injected GameService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        api_key_header (str): The API key header.

    Returns:
        GameCreated: The details of the created game.
    """

    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Create game - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Game creation",
        schema.dict(),
        service_log,
        api_key,
        oauth_user_id,
    )
    try:
        response = await service.create(schema, api_key, oauth_user_id)
        data_to_log = {"body": schema.dict(), "gameId": str(response.gameId)}
        await add_log(
            "game",
            "SUCCESS",
            "Game creation successful",
            data_to_log,
            service_log,
            api_key,
            oauth_user_id,
        )
        return response
    except Exception as e:
        await add_log(
            "game",
            "ERROR",
            "Game creation failed",
            {"error": str(e)},
            service_log,
            api_key,
            oauth_user_id,
        )
        raise e


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
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def patch_game(
    gameId: UUID,
    schema: PatchGame,
    service: GameService = Depends(Provide[Container.game_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Update a game by its ID.

    Args:
        gameId (UUID): The ID of the game to update.
        schema (PatchGame): The schema for updating the game.
        service (GameService): Injected GameService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ResponsePatchGame: The updated game details.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Update game by ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Game update by ID",
        {"gameId": str(gameId), "body": schema.dict()},
        service_log,
        api_key,
        oauth_user_id,
    )

    try:
        response = await service.patch_game_by_id(gameId, schema)
        data_to_log = {"gameId": str(gameId), "body": schema.dict()}
        await add_log(
            "game",
            "SUCCESS",
            "Game update successful",
            data_to_log,
            service_log,
            api_key,
            oauth_user_id,
        )
        return response
    except Exception as e:
        await add_log(
            "game",
            "ERROR",
            "Game update failed",
            {"error": str(e)},
            service_log,
            api_key,
            oauth_user_id,
        )
        raise e


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
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_strategy_by_gameId(
    gameId: UUID,
    service: GameService = Depends(Provide[Container.game_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve the strategy associated with a game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (GameService): Injected GameService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        Strategy: The strategy associated with the specified game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Get strategy by game ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Strategy retrieval by game ID",
        {"gameId": str(gameId)},
        service_log,
        api_key,
        oauth_user_id,
    )

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
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def create_task(
    gameId: UUID,
    create_query: CreateTaskPost = Body(..., example=CreateTaskPost.example()),
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Create a task for a specific game.

    Args:
        gameId (UUID): The ID of the game.
        create_query (CreateTaskPost): The schema for creating a task.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        CreateTaskPostSuccesfullyCreated: The details of the created task.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Create task - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Task creation",
        {"gameId": str(gameId), "body": create_query.dict()},
        service_log,
        api_key,
        oauth_user_id,
    )
    try:
        response = await service.create_task_by_game_id(gameId, create_query, api_key)
        data_to_log = {"gameId": str(gameId), "body": create_query.dict()}
        await add_log(
            "game",
            "SUCCESS",
            "Task creation successful",
            data_to_log,
            service_log,
            api_key,
            oauth_user_id,
        )
        return response
    except Exception as e:
        await add_log(
            "game",
            "ERROR",
            "Task creation failed",
            {"error": str(e)},
            service_log,
            api_key,
            oauth_user_id,
        )
        raise e


summary_create_tasks_bulk = "Create Multiple New Tasks"
description_create_tasks_bulk = """
## Create Multiple New Tasks (Bulk)
### This endpoint allows for the bulk creation of multiple new tasks within a specific game using the game's ID.
<sub>**Id_endpoint:** create_tasks_bulk</sub>"""  # noqa


@router.post(
    "/{gameId}/tasks/bulk",
    response_model=CreateTasksPostBulkCreated,
    summary=summary_create_tasks_bulk,
    description=description_create_tasks_bulk,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def create_tasks_bulk(
    gameId: UUID,
    create_query: CreateTasksPost = Body(...,
                                         example=CreateTasksPost.example()),
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Create multiple tasks for a specific game (bulk creation).

    Args:
        gameId (UUID): The ID of the game.
        create_query (CreateTasksPost): The schema for creating multiple tasks.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[CreateTaskPostSuccesfullyCreated]: The details of the created
          tasks.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Bulk task creation - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    succesfully_created = []
    failed_to_create = []
    await add_log(
        "game",
        "INFO",
        "Bulk task creation",
        {"gameId": str(gameId), "body": create_query.dict()},
        service_log,
        api_key,
        oauth_user_id,
    )

    for task in create_query.tasks:
        try:
            created_task = service.create_task_by_game_id(
                gameId, task, api_key)
            succesfully_created.append(created_task)
        except Exception as e:
            failed_to_create.append({"task": task, "error": str(e)})
    if len(failed_to_create) > 0:
        await add_log(
            "game",
            "ERROR",
            "Bulk task creation failed",
            {
                "gameId": str(gameId),
                "body": create_query.dict(),
                "failed_tasks": failed_to_create,
            },
            service_log,
            api_key,
            oauth_user_id,
        )
    if len(succesfully_created) > 0:
        await add_log(
            "game",
            "SUCCESS",
            "Bulk task creation successful",
            {
                "gameId": str(gameId),
                "body": create_query.dict(),
                "succesfully_created": succesfully_created,
            },
            service_log,
            api_key,
            oauth_user_id,
        )

    return {
        "succesfully_created": succesfully_created,
        "failed_to_create": failed_to_create,
    }


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
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_task_list(
    gameId: UUID,
    find_query: PostFindTask = Depends(),
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve a list of tasks for a specific game.

    Args:
        gameId (UUID): The ID of the game.
        find_query (PostFindTask): Query parameters for finding tasks.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        FoundTasks: A result set containing the tasks.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Task list retrieval - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Task list retrieval",
        {"gameId": str(gameId), "body": find_query.dict()},
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_tasks_list_by_gameId(gameId, find_query)


summary_get_task_by_gameId_taskId = (
    "Retrieve Task by Game ID and External Task ID"  # noqa
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
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_task_by_gameId_taskId(
    gameId: UUID,
    externalTaskId: str,
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve a task by its external game ID and external task ID.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        CreateTaskPostSuccesfullyCreated: The details of the specified task.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Task retrieval by game ID and external task ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )

    await add_log(
        "game",
        "INFO",
        "Task retrieval by game ID and external task ID",
        {"gameId": str(gameId), "externalTaskId": externalTaskId},
        service_log,
        api_key,
        oauth_user_id,
    )

    return service.get_task_by_externalGameId_externalTaskId(
        str(gameId), externalTaskId
    )


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
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_by_gameId(
    gameId: UUID,
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve points associated with a specific game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        AllPointsByGame: The points details for the specified game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Points retrieval by game ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Points retrieval by game ID",
        {"gameId": str(gameId)},
        service_log,
        api_key,
        oauth_user_id,
    )

    return service.get_points_by_gameId(gameId)


summary_get_points_by_gameId_with_details = "Retrieve Points by Game ID with Details"
description_get_points_by_gameId_with_details = """
## Retrieve Points by Game ID with Details
### This endpoint retrieves the points details associated with a specific game by its ID.
<sub>**Id_endpoint:** get_points_by_gameId_with_details</sub>"""  # noqa


@router.get(
    "/{gameId}/points/details",
    response_model=AllPointsByGameWithDetails,
    summary=summary_get_points_by_gameId_with_details,
    description=description_get_points_by_gameId_with_details,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_by_gameId_with_details(
    gameId: UUID,
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve points associated with a specific game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        AllPointsByGame: The points details for the specified game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Points retrieval by game ID with details - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Points retrieval by game ID with details",
        {"gameId": str(gameId)},
        service_log,
        api_key,
        oauth_user_id,
    )

    return service.get_points_by_gameId_with_details(gameId)


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
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_of_user_in_game(
    gameId: UUID,
    externalUserId: str,
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve points of a user in a specific game.

    Args:
        gameId (UUID): The ID of the game.
        externalUserId (str): The external user ID.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[PointsAssignedToUser]: The points details of the user in the
          specified game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "User points retrieval by game ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "User points retrieval by game ID",
        {"gameId": str(gameId), "externalUserId": externalUserId},
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_points_of_user_in_game(gameId, externalUserId)


summary_user_action = "User Action"
description_user_action = """
## User Action
### This endpoint allows for the assignment of points to a user for a specific task within a game.
<sub>**Id_endpoint:** user_action_in_task</sub>
"""  # noqa


@router.post(
    "/{gameId}/tasks/{externalTaskId}/action",
    response_model=ResponseAddActionDidByUserInTask,
    summary=summary_user_action,
    description=description_user_action,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def user_action_in_task(
    gameId: UUID,
    externalTaskId: str,
    schema: AddActionDidByUserInTask = Body(...),
    service: UserActionsService = Depends(
        Provide[Container.user_actions_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Register a user action in a task within a game. This endpoint is used to
    assign points to a user for a specific task within a game, when the game
    requires it.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        schema (AddActionDidByUserInTask): The schema for adding an action.
        service (UserActionsService): Injected UserActionsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ResponseAddActionDidByUserInTask: The details of the action added.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "User action in task - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "User action in task",
        {
            "gameId": str(gameId),
            "externalTaskId": externalTaskId,
            "body": schema.dict(),
        },
        service_log,
        api_key,
        oauth_user_id,
    )

    return service.user_add_action_in_task(gameId, externalTaskId, schema, api_key)


summary_assign_points_to_user = "Assign Points to User"
description_assign_points_to_user = """
## Assign Points to User
### This endpoint assigns points to a user for a specific task within a game.
<sub>**Id_endpoint:** assign_points_to_user</sub>
"""  # noqa


@router.post(
    "/{gameId}/tasks/{externalTaskId}/points",
    response_model=AssignedPointsToExternalUserId,
    summary=summary_assign_points_to_user,
    description=description_assign_points_to_user,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def assign_points_to_user(
    gameId: UUID,
    externalTaskId: str,
    schema: AsignPointsToExternalUserId = Body(...),
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Assign points to a user for a specific task in a game.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        schema (AsignPointsToExternalUserId): The schema for assigning points.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        AssignedPointsToExternalUserId: The details of the points assigned.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Points assignment to user - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Points assignment to user",
        {
            "gameId": str(gameId),
            "externalTaskId": externalTaskId,
            "body": schema.dict(),
        },
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.assign_points_to_user(gameId, externalTaskId, schema, api_key)

summary_simulate_assign_point = "Simulate Assign Points"
description_simulate_assign_point = """
## Simulate Assign Points
### This endpoint simulates the assignment of points to a user for a specific task within a game without actually assigning the points.
<sub>**Id_endpoint:** simulate_assign_point</sub>
"""  # noqa


@router.post(
    "/{gameId}/tasks/{externalTaskId}/points/simulate",
    response_model=SimulatedPointsAssignedToUser,
    summary=summary_simulate_assign_point,
    description=description_simulate_assign_point,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def simulate_assign_point(
    gameId: UUID,
    externalTaskId: str,
    schema: AsignPointsToExternalUserId = Body(...),
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Simulate the assignment of points to a user for a specific task in a game.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        schema (AsignPointsToExternalUserId): The schema for assigning points.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService
          dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        AssignedPointsToExternalUserId: The details of the points that would be
          assigned.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Points simulation - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )


summary_get_points_by_task_id = "Retrieve Points by Task ID"
description_get_points_by_task_id = """
## Retrieve Points by Task ID
### This endpoint retrieves the points details associated with a specific task using the game's ID and the external task ID.
<sub>**Id_endpoint:** get_points_by_task_id</sub>"""  # noqa


@router.get(
    "/{gameId}/tasks/{externalTaskId}/points",
    response_model=List[PointsAssignedToUser],
    summary=summary_get_points_by_task_id,
    description=description_get_points_by_task_id,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_by_task_id(
    gameId: UUID,
    externalTaskId: str,
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve points by task ID.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[PointsAssignedToUser]: The points details for the specified task.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Points retrieval by task ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Points retrieval by task ID",
        {"gameId": str(gameId), "externalTaskId": externalTaskId},
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_points_by_task_id(gameId, externalTaskId)


summary_get_points_of_user_by_task_id = "Retrieve User Points by Task ID"
description_get_points_of_user_by_task_id = """
## Retrieve User Points by Task ID
### This endpoint retrieves the points details of a user associated with a specific task using the game's ID and the user's external ID.
<sub>**Id_endpoint:** get_points_of_user_by_task_id</sub>"""  # noqa


@router.get(
    "/{gameId}/tasks/{externalTaskId}/users/{externalUserId}/points",
    response_model=PointsAssignedToUser,
    summary=summary_get_points_of_user_by_task_id,
    description=description_get_points_of_user_by_task_id,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_of_user_by_task_id(
    gameId: UUID,
    externalTaskId: str,
    externalUserId: str,
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve points of a user by task ID.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        externalUserId (str): The external user ID.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        PointsAssignedToUser: The points details of the user for the specified
          task.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "User points retrieval by task ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "User points retrieval by task ID",
        {
            "gameId": str(gameId),
            "externalTaskId": externalTaskId,
            "externalUserId": externalUserId,
        },
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_points_of_user_by_task_id(gameId, externalTaskId, externalUserId)


summary_get_points_by_task_id_with_details = (
    "Retrieve Detailed Points by Task ID"  # noqa
)
description_get_points_by_task_id_with_details = """
## Retrieve Detailed Points by Task ID
### This endpoint retrieves detailed points information associated with a specific task using the game's ID and the external task ID.
<sub>**Id_endpoint:** get_points_by_task_id_with_details</sub>
"""  # noqa


@router.get(
    "/{gameId}/tasks/{externalTaskId}/points/details",
    response_model=List[dict],  # WIP FIX
    summary=summary_get_points_by_task_id_with_details,
    description=description_get_points_by_task_id_with_details,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_points_by_task_id_with_details(
    gameId: UUID,
    externalTaskId: str,
    service: TaskService = Depends(Provide[Container.task_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve detailed points by task ID.

    Args:
        gameId (UUID): The ID of the game.
        externalTaskId (str): The external task ID.
        service (TaskService): Injected TaskService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        List[dict]: Detailed points information for the specified task.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Detailed points retrieval by task ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Detailed points retrieval by task ID",
        {"gameId": str(gameId), "externalTaskId": externalTaskId},
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_points_by_task_id_with_details(gameId, externalTaskId)


summary_get_users_by_gameId = "Retrieve Users by Game ID"
description_get_users_by_gameId = """
## Retrieve Users by Game ID
### This endpoint retrieves the list of users associated with a specific game using the game's ID.
<sub>**Id_endpoint:** get_users_by_gameId</sub>
"""  # noqa


@router.get(
    "/{gameId}/users",
    response_model=ListTasksWithUsers,
    summary=summary_get_users_by_gameId,
    description=description_get_users_by_gameId,
    dependencies=[Depends(auth_api_key_or_oauth2)],
)
@inject
async def get_users_by_gameId(
    gameId: UUID,
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
    service_oauth: OAuthUsersService = Depends(
        Provide[Container.oauth_users_service]),
    token: str = Depends(oauth_2_scheme),
    api_key_header: str = Depends(ApiKeyService.get_api_key_header),
):
    """
    Retrieve users associated with a game by its ID.

    Args:
        gameId (UUID): The ID of the game.
        service (UserPointsService): Injected UserPointsService dependency.
        service_log (LogsService): Injected LogsService dependency.
        service_oauth (OAuthUsersService): Injected OAuthUsersService dependency.
        token (str): The OAuth2 token.
        api_key_header (str): The API key header.

    Returns:
        ListTasksWithUsers: The list of users associated with the specified
          game.
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id = None
    if token:
        token_data = await valid_access_token(token)
        oauth_user_id = token_data.data["sub"]
        if service_oauth.get_user_by_sub(oauth_user_id) is None:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=oauth_user_id,
                status="active",
            )
            await service_oauth.add(create_user)
            await add_log(
                "game",
                "INFO",
                "Users retrieval by game ID - User created",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key,
                oauth_user_id,
            )
    await add_log(
        "game",
        "INFO",
        "Users retrieval by game ID",
        {"gameId": str(gameId)},
        service_log,
        api_key,
        oauth_user_id,
    )
    return service.get_users_by_gameId(gameId)
