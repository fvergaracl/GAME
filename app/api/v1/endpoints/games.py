from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Body

from app.core.container import Container
from app.schema.games_schema import (FindGameById, FindGameResult,
                                     GameCreated, PatchGame,
                                     PostCreateGame, PostFindGame,
                                     ResponsePatchGame)
from app.schema.strategy_schema import Strategy
from app.services.game_service import GameService

from app.schema.task_schema import (CreateTaskPost,
                                    CreateTaskPostSuccesfullyCreated,
                                    FoundTasks, PostFindTask)
from app.services.task_service import TaskService

router = APIRouter(
    prefix="/games",
    tags=["games"],
)


summary_get_games_list = "Get Games List"
description_get_games_list = """
## Find Game
### Find all games and params
"""


@router.get(
    "",
    response_model=FindGameResult,
    description=description_get_games_list,
    summary=summary_get_games_list,
)
@inject
def get_games_list(
    schema: PostFindGame = Depends(),
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.get_all_games(schema)


summary_get_game_by_id = "Get Game by externalGameId"
description_get_game_by_id = """
Get Game by externalGameId

"""


@router.get(
    "/{id}",
    response_model=FindGameById,
    description=description_get_game_by_id,
    summary=summary_get_game_by_id,
)
@inject
def get_game_by_id(
    externalGameId: str,
    service: GameService = Depends(Provide[Container.game_service]),
):

    response = service.get_by_id(externalGameId)
    return response


summary_create_game = "Create Game"
description_create_game = """
Create Game
"""


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
    return service.create(schema)


summary_patch_game = "Update Game"
description_patch_game = """
Update Game
can update even the GameParams
"""


@router.patch("/{externalGameId}", response_model=ResponsePatchGame)
@inject
def patch_game(
    externalGameId: str,
    schema: PatchGame,
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.pacth_game_by_externalGameId(externalGameId, schema)


summary_get_strategy_by_externalGameId = "Get Strategy by externalGameId"
description_get_strategy_by_externalGameId = """
Get Strategy by externalGameId
"""


@router.get(
    "/{externalGameId}/strategy",
    response_model=Strategy,
    summary=summary_get_strategy_by_externalGameId,
    description=description_get_strategy_by_externalGameId,
)
@inject
def get_strategy_by_externalGameId(
    externalGameId: str,
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.get_strategy_by_externalGameId(externalGameId)


summary_create_task = "Create Task"
description_create_task = """
Create Task in a game using externalGameId

"""


@router.post(
    "/{externalGameId}/tasks",
    response_model=CreateTaskPostSuccesfullyCreated
)
@inject
def create_task(
    externalGameId: str,
    create_query: CreateTaskPost = Body(..., example=CreateTaskPost.example()),
    service: TaskService = Depends(Provide[Container.task_service]),
):
    return service.create_task_by_externalGameId(externalGameId, create_query)


summary_get_task_list = "Get Task List"
description_get_task_list = """
Get Task List
"""


@router.get(
    "/{externalGameId}/tasks",
    response_model=FoundTasks,
    summary=summary_get_task_list,
    description=description_get_task_list,
)
@inject
def get_task_list(
    externalGameId: str,
    find_query: PostFindTask = Depends(),
    service: TaskService = Depends(Provide[Container.task_service]),
):
    return service.get_tasks_list_by_externalGameId(externalGameId, find_query)


summary_get_task_by_externalGameId_taskId = "Get Task by externalGameId and externalTaskId"  # noqa
description_get_task_by_externalGameId_taskId = """
Get Task by externalGameId and externalTaskId
"""


@router.get(
    "/{externalGameId}/tasks/{externalTaskId}",
    response_model=CreateTaskPostSuccesfullyCreated,
    summary=summary_get_task_by_externalGameId_taskId,
    description=description_get_task_by_externalGameId_taskId,
)
@inject
def get_task_by_externalGameId_taskId(
    externalGameId: str,
    externalTaskId: str,
    service: TaskService = Depends(Provide[Container.task_service]),
):
    return service.get_task_by_externalGameId_externalTaskId(
        externalGameId, externalTaskId)
