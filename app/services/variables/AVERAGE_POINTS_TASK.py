from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.services.base_service import BaseService
from app.services.variables.sub_variables import get_sub_variables_by_name
from app.core.exceptions import NotFoundError


class AveragePointsTaskService(BaseService):

    def __init__(
            self,
            task_repository: TaskRepository,
            user_points_repository: UserPointsRepository

    ):
        self.variable_name = "@AVG_POINTS_TASK"
        self.variable_description = "Average points of task by externalTaskId"
        self.sub_variables = [
            get_sub_variables_by_name("#EXTERNAL_TASK_ID")
        ]
        self.task_repository = task_repository
        self.user_points_repository = user_points_repository
        super().__init__(
            task_repository,
            user_points_repository,
            self.variable_name,
            self.variable_description,
            self.sub_variables
        )

    def average_points_task(self, externalTaskId):
        task = self.task_repository.read_by_column(
            "externalTaskId",
            externalTaskId,
            not_found_message="Task not found with externalTaskId : {externalTaskId} "
        )
        user_points = self.user_points_repository.read_by_taskId(task.id)
        if len(user_points) == 0:
            raise NotFoundError(
                detail=f"User points not found with taskId : {task.id}")
        sum_points = 0
        for user_point in user_points:
            sum_points += user_point.points
        average_points = sum_points / len(user_points)
        return average_points
