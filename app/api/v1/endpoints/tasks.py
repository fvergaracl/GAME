from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.task_schema import (CreateTaskPost,
                                    CreateTaskPostSuccesfullyCreated,
                                    FoundTaskById, GetTaskById,
                                    TaskPointsResponse)
from app.services.task_service import TaskService

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

game_task_router = APIRouter(
    prefix="/game",
    tags=["tasks"],
)


# summary_get_tasks_list = "Get Tasks List, strategies and userPoints by task ID"
# description_get_tasks_list = """
# ## Find Task
# ### Find all tasks and params by id
# """


# @router.get(
#     "/{taskId}",
#     response_model=FoundTaskById,
#     summary=summary_get_tasks_list,
#     description=description_get_tasks_list,
# )
# @inject
# def get_task_detail_by_id(
#     schema: GetTaskById = Depends(),
#     service: TaskService = Depends(Provide[Container.task_service]),
# ):
#     return service.get_task_detail_by_id(schema)


# # get points by task id
# summary_get_points_by_task_id = "Get points by task id"
# description_get_points_by_task_id = """
# ## Get points by task id
# ### Get points by task id
# """


# @router.get(
#     "/{taskId}/points",
#     response_model=TaskPointsResponse,
#     summary=summary_get_points_by_task_id,
#     description=description_get_points_by_task_id,
# )
# @inject
# def get_points_by_task_id(
#     schema: GetTaskById = Depends(),
#     service: TaskService = Depends(Provide[Container.task_service]),
# ):
#     return service.get_points_by_task_id(schema)


summary_create_task = "Create Task"
description_create_task = """
Create Task in a game using externalGameId

"""


@game_task_router.post("/{externalGameId}/tasks", response_model=CreateTaskPostSuccesfullyCreated)
@inject
def create_task(
    externalGameId: str,
    create_query: CreateTaskPost,
    service: TaskService = Depends(Provide[Container.task_service]),
):
    return service.create_task_by_externalGameId(externalGameId, create_query)
