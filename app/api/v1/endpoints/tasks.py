from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.task_schema import FindTaskResult, FindTask
from app.schema.games_params_schema import BaseGameParams
from app.services.task_service import TaskService
from app.services.game_params_service import GameParamsService

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


@router.get("/{gameId}", response_model=FindTaskResult)
@inject
def get_tasks_list__by_externalGameId(
    find_query: FindTask = Depends(),
    service: TaskService = Depends(Provide[Container.task_service]),
):
    return service.get_list(find_query)
