from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Body

from app.core.container import Container
from app.schema.task_schema import (AsignPointsToExternalUserId,
                                    CreateTaskPostSuccesfullyCreated,
                                    FoundTaskById, GetTaskById,
                                    TaskPointsResponse)
from app.services.task_service import TaskService
from app.services.user_points_service import UserPointsService

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

game_task_router = APIRouter(
    prefix="/game",
    tags=["tasks"],
)


summary_assing_points_to_user = "Assign points to user"
description_assing_points_to_user = """
## Assign points to user
### Assign points to user
"""


@router.post(
    "/{externalTaskId}/points",
    response_model=TaskPointsResponse,
    summary=summary_assing_points_to_user,
    description=description_assing_points_to_user,
)
@inject
def assign_points_to_user(
    externalTaskId: str,
    schema: AsignPointsToExternalUserId = Body(...),
    service: UserPointsService = Depends(
        Provide[Container.user_points_service]),
):
    return service.assign_points_to_user(externalTaskId, schema)


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
