from app.repository.uptime_logs_repository import UptimeLogsRepository
from app.services.base_service import BaseService


class UptimeLogsService(BaseService):
    """
    Service class for Uptime Logs.

    Attributes:
        uptime_logs_repository (UptimeLogsRepository): Repository instance
          for Uptime Logs.
    """

    def __init__(self, uptime_logs_repository: UptimeLogsRepository):
        """
        Initializes the UptimeLogsService with the provided repository.

        Args:
            uptime_logs_repository (UptimeLogsRepository): The repository
              instance.
        """
        self.uptime_logs_repository = uptime_logs_repository
        super().__init__(uptime_logs_repository)
