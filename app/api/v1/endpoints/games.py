from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.games_schema import FindGameResult, CreateGame, UpdateGame, Game, FindGame
from app.services.game_service import GameService

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


@router.get("/{externalGameId}", response_model=Game)
@inject
def get_game_by_externalId(
    externalGameId: str,
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.get_by_externalId(externalGameId)


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
