from app.repository.logs_repository import LogsRepository
from app.services.base_service import BaseService


class LogsService(BaseService):
    """
    Service class for managing logs records.

    Attributes:
        logs_repository (LogsRepository): Repository instance for logs.

    """

    def __init__(self, logs_repository: LogsRepository):
        """
        Initializes the LogsService with the provided repositories and
          services.

        Args:
            logs_repository: The logs repository instance.
        """
        self.logs_repository = logs_repository
        super().__init__(logs_repository)
