from fastapi import APIRouter
router = APIRouter(
    prefix="/tasks",
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
