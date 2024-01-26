from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from uuid import UUID

from app.core.container import Container
from app.schema.games_schema import (
    PostFindGame,
    FindGameResult,
    PostCreateGame,
    GameCreated,
    UpdateGame,
    GameUpdated,
    Game
)
from app.services.game_service import GameService

router = APIRouter(

    prefix="/games",
    tags=["games"],
)


summary_get_games_list = "Get Games List"
description_get_games_list = """
## Find Game
### Find game by externalGameId
"""


@router.get(
    "/",
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


summary_get_game_by_id = "Get Game by Id"
description_get_game_by_id = """
## Get Game by Id
### Get game by id 
"""


@router.get(
    "/{id}",
    response_model=Game,
    description=description_get_game_by_id,
    summary=summary_get_game_by_id
)
@inject
def get_game_by_id(
    id: UUID,
    service: GameService = Depends(Provide[Container.game_service]),
):

    response = service.get_by_id(id)
    response.id = str(response.id)
    return response


summary_create_game = "Create Game"
description_create_game = """
## Create Game
"""


@router.post(
    "/",
    response_model=GameCreated,
    summary=summary_create_game,
    description=description_create_game
)
@inject
def create_game(
    schema: PostCreateGame,
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.create(schema)


########################## Línea de corte #####################################


@router.put("/{id}", response_model=GameUpdated)
@inject
def update_game(
    id: str,
    schema: UpdateGame,
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.update(id, schema)
