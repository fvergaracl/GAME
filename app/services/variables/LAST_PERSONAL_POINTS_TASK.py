from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.services.variables.variableBase import VariableBase
from app.services.variables.sub_variables import get_sub_variables_by_name
from app.core.exceptions import NotFoundError


class LastPersonalPointsTaskService(VariableBase):

    def __init__(
            self,
            task_repository: TaskRepository,
            user_points_repository: UserPointsRepository

    ):
        self.variable_name = "@LAST_PERSONAL_POINT_TASK"
        self.variable_description = "Last personal point of task by externalTaskId"
        self.sub_variables = [
            get_sub_variables_by_name("#EXTERNAL_TASK_ID"),
            get_sub_variables_by_name("#EXTERNAL_USER_ID")
        ]
        self.task_repository = task_repository
        self.user_points_repository = user_points_repository
        super().__init__(
            self.variable_name,
            self.variable_description,
            self.sub_variables
        )

    def last_personal_point_task(self, externalTaskId, externalUserId):
        task = self.task_repository.read_by_column(
            "externalTaskId",
            externalTaskId,
            not_found_message="Task not found with externalTaskId : {externalTaskId} "
        )
        user_points = self.user_points_repository.read_by_taskId_and_externalUserId(
            task.id, externalUserId)
        if len(user_points) == 0:
            raise NotFoundError(
                detail=f"User points not found with taskId : {task.id} and externalUserId : {externalUserId}")
        return user_points[-1].points
