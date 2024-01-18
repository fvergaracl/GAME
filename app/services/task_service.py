from app.repository.task_repository import TaskRepository
from app.services.base_service import BaseService


class TaskService(BaseService):
    def __init__(self, task_repository: TaskRepository):
        self.task_repository = task_repository
        super().__init__(task_repository)
