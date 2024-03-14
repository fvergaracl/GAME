from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Body

from app.core.container import Container
from app.schema.task_schema import (AsignPointsToExternalUserId,
                                    CreateTaskPostSuccesfullyCreated,
                                    FoundTaskById, GetTaskById,
                                    AssignedPointsToExternalUserId)
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
