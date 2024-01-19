from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.task_schema import FindTaskResult, FindTaskByExternalGameID, CreateTaskPost, CreateTaskPostSuccesfullyCreated
from app.schema.games_params_schema import BaseGameParams
from app.services.task_service import TaskService
from app.services.game_params_service import GameParamsService

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


@router.get("/{externalGameId}", response_model=FindTaskResult)
@inject
def get_tasks_list_by_externalGameId(
    find_query: FindTaskByExternalGameID = Depends(),
    service: TaskService = Depends(Provide[Container.task_service]),
):
    return service.get_tasks_list_by_externalGameId(find_query)


@router.post("/", response_model=CreateTaskPostSuccesfullyCreated)
@inject
def create_task(
    create_query: CreateTaskPost,
    service: TaskService = Depends(Provide[Container.task_service]),
):
    return service.create_task_by_externalGameId(create_query)
