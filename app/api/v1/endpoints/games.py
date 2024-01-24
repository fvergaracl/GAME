from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.games_schema import (
    PostFindGame,
    FindGameResult,
    BaseGameResult,
    CreateGame,
    UpdateGame,
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
    print(' ........................ ')
    print("schema", schema)
    print(' ........................ ')
    return service.get_list(schema)


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
    id: str,
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.get_by_id(id)


@router.post("/", response_model=Game)
@inject
def create_game(
    schema: CreateGame,
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.create(schema)


@router.put("/{id}", response_model=Game)
@inject
def update_game(
    id: int,
    schema: UpdateGame,
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.update(id, schema)
