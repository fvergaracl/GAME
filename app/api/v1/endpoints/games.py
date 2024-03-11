from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.games_schema import (FindGameById, FindGameResult,
                                     FindTaskGameById, GameCreated, PatchGame,
                                     PostCreateGame, PostFindGame,
                                     ResponsePatchGame)
from app.services.game_service import GameService

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


summary_get_game_by_id = "Get Game by externalId"
description_get_game_by_id = """
Get Game by externalId

"""


@router.get(
    "/{id}",
    response_model=FindGameById,
    description=description_get_game_by_id,
    summary=summary_get_game_by_id,
)
@inject
def get_game_by_id(
    externalId: str,
    service: GameService = Depends(Provide[Container.game_service]),
):

    response = service.get_by_id(externalId)
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
    schema: PostCreateGame,
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.create(schema)



# summary_patch_game = "Update Game"
# description_patch_game = """
# Update Game
# can update even the GameParams
# """


# @router.patch("/{id}", response_model=ResponsePatchGame)
# @inject
# def patch_game(
# id: str,
# schema: PatchGame,
# service: GameService = Depends(Provide[Container.game_service]),
# ):
# return service.patch_game_by_id(id, schema)


# summary_get_task_by_id_game = "Get Task by Id Game"
# description_get_task_by_id_game = """
# Get Task by Id Game
# """


# @router.get(
# "/{id}/tasks",
# response_model=FindTaskGameById,
# description=description_get_task_by_id_game,
# summary=summary_get_task_by_id_game,
# )
# @inject
# def get_task_by_id_game(
# id: UUID,
# service: GameService = Depends(Provide[Container.game_service]),
# ):

# response = service.get_tasks_by_gameId(id)
# return response
