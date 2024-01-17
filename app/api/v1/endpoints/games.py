from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.games_schema import FindGameResult, CreateGame, Game, FindGame

from app.services.game_service import GameService
from app.services.game_params_service import GameParamsService

router = APIRouter(
    prefix="/games",
    tags=["games"],
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


@router.post("/", response_model=Game)
@inject
def create_game(
    schema: CreateGame,
    service: GameService = Depends(Provide[Container.game_service]),
    serviceGameParams: GameParamsService = Depends(
        Provide[Container.game_service]),
):
    params = schema.params
    if params:
        del schema.params
        game = service.create(schema)
        for param in params:
            param.gameID = game.id
            serviceGameParams.add(param)
        return game
    return service.create(schema)
