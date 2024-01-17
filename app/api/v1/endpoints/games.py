from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.games_schema import FindGameResult, CreateGame, UpdateGame, Game, FindGame
from app.schema.games_params_schema import BaseGameParams
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


# @router.post("/", response_model=Game)
# @inject
# def create_game(
#     schema: CreateGame,
#     service: GameService = Depends(Provide[Container.game_service]),
#     service_game_params: GameParamsService = Depends(
#         Provide[Container.game_service]),
# ):
#     params = schema.params
#     print('******************************')
#     print(params)
#     if params:
#         print('******************************1')
#         del schema.params
#         game = service.create(schema)
#         print('******************************2')
#         print(game)
#         for param in params:
#             print('******************************3')
#             print(param)

#             param.gameID = game.id
#             game_params_result = service_game_params.add(param)
#             print('******************************4')
#             print(game_params_result)
#         return game
#     return service.create(schema)


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
