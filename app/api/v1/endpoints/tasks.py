from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.games_schema import FindGameResult, CreateGame, UpdateGame, Game, FindGame
from app.schema.games_params_schema import BaseGameParams
from app.services.game_service import GameService
from app.services.game_params_service import GameParamsService

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


@router.get("/", response_model=FindGameResult)
@inject
def get_games_list(
    find_query: FindGame = Depends(),
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.get_list(find_query)


@router.get("/externalId/{externalGameID}", response_model=Game)
@inject
def get_game_by_externalId(
    externalGameID: str,
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.get_by_externalId(externalGameID)
