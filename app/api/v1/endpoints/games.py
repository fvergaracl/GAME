from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.games_schema import FindGameResult, FindGame

from app.services.game_service import GameService

router = APIRouter(
    prefix="/games",
    tags=["auth"],
)


@router.get("/", response_model=FindGameResult)
@inject
def get_games_list(
    find_query: FindGame = Depends(),
    service: GameService = Depends(Provide[Container.game_service]),
):
    return service.get_list(find_query)
