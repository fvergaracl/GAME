from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.services.variables.variableBase import VariableBase
from app.services.variables.sub_variables import get_sub_variables_by_name
from app.core.exceptions import NotFoundError


class AveragePointsTaskService(VariableBase):

    def __init__(
            self,
            task_repository: TaskRepository,
            user_points_repository: UserPointsRepository

    ):
        self.variable_name = "@AVG_POINTS_TASK_BY_USER"
        self.variable_description = "Average points of task by externalTaskId"
        self.sub_variables = [
            get_sub_variables_by_name("#EXTERNAL_TASK_ID")
        ]
        self.task_repository = task_repository
        self.user_points_repository = user_points_repository
        super().__init__(
            self.variable_name,
            self.variable_description,
            self.sub_variables
        )

    def average_points_task_by_user(self, externalTaskId):
        task = self.task_repository.read_by_column(
            "externalTaskId",
            externalTaskId,
            not_found_message="Task not found with externalTaskId : {externalTaskId} "
        )
        user_points = self.user_points_repository.read_by_column(
            "taskId",
            task.id,
            only_one=False,
            not_found_raise_exception=False
        )
        if len(user_points) == 0:
            return 0
        sum_points = 0
        for user_point in user_points:
            sum_points += user_point.points
        return sum_points / len(user_points)
