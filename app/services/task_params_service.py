from app.core.exceptions import ConflictError, NotFoundError
from app.repository.task_params_repository import TaskParamsRepository
from app.repository.task_repository import TaskRepository
from app.services.base_service import BaseService


class TaskParamsService(BaseService):
    """
    Service class for managing tasks.

    Attributes:
        task_params_repository (TaskParamsRepository): Repository instance for
          task parameters.
    """

    def __init__(
        self,
        task_params_repository: TaskParamsRepository,
    ):
        """
        Initializes the TaskService with the provided repositories and
          services.

        Args:
            task_params_repository (TaskParamsRepository): The task parameters
              repository instance.
        """

        self.task_params_repository = task_params_repository
        super().__init__(task_params_repository)
