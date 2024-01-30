from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from uuid import UUID

from app.core.container import Container
from app.schema.task_schema import (
    GetTaskById,
    FindTaskResult,
    FindTaskByExternalGameID,
    FoundTaskById,
    CreateTaskPost,
    CreateTaskPostSuccesfullyCreated
)
from app.services.task_service import TaskService

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

game_task_router = APIRouter(
    prefix="/game",
    tags=["tasks"],
)


summary_get_tasks_list = "Get Tasks List, strategies and userPoints by task ID "
description_get_tasks_list = """
## Find Task
### Find all tasks and params by id
"""


@router.get(
    "/{taskId}",
    response_model=FoundTaskById,
    summary=summary_get_tasks_list,
    description=description_get_tasks_list,
)
@inject
def get_task_detail_by_id(
    schema: GetTaskById = Depends(),
    service: TaskService = Depends(
        Provide[Container.task_service]),
):
    return service.get_task_detail_by_id(schema)


@game_task_router.post("/{id}/tasks", response_model=CreateTaskPostSuccesfullyCreated)
@inject
def create_task(
    id: UUID,
    create_query: CreateTaskPost,
    service: TaskService = Depends(Provide[Container.task_service]),
):
    return service.create_task_by_game_id(id, create_query)
