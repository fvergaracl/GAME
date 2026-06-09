from typing import Any

from app.repository.dashboard_repository import DashboardRepository
from app.repository.game_repository import GameRepository
from app.repository.logs_repository import LogsRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_actions_repository import UserActionsRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.services.base_service import BaseService


class DashboardService(BaseService):
    """
    Service class for API keys.

    Attributes:
        dashboard_repository (DashboardRepository): The repository instance.
    """

    def __init__(
        self,
        dashboard_repository: DashboardRepository,
        game_repository: GameRepository,
        task_repository: TaskRepository,
        user_repository: UserRepository,
        logs_repository: LogsRepository,
        user_points_repository: UserPointsRepository,
        user_actions_repository: UserActionsRepository,
    ) -> None:
        """
        Initializes the DashboardService with the provided repository.

        Args:
            dashboard_repository (DashboardRepository): The repository
              instance.
        """
        self.dashboard_repository = dashboard_repository
        self.game_repository = game_repository
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.logs_repository = logs_repository
        self.user_points_repository = user_points_repository
        self.user_actions_repository = user_actions_repository
        super().__init__(dashboard_repository)

    async def get_dashboard_summary(self, start_date, end_date, group_by) -> Any:
        """
        Return the dashboard activity summary for a date range.

        Args:
            start_date: Inclusive lower bound of the reporting window.
            end_date: Inclusive upper bound of the reporting window.
            group_by: Bucketing granularity (e.g. ``"day"``/``"month"``).

        Returns:
            Any: Aggregated summary metrics produced by the repository.
        """
        return await self.dashboard_repository.get_dashboard_summary(
            start_date, end_date, group_by
        )

    async def get_dashboard_summary_logs(self, start_date, end_date, group_by) -> Any:
        """
        Return the dashboard log-activity summary for a date range.

        Args:
            start_date: Inclusive lower bound of the reporting window.
            end_date: Inclusive upper bound of the reporting window.
            group_by: Bucketing granularity (e.g. ``"day"``/``"month"``).

        Returns:
            Any: Aggregated log metrics produced by the repository.
        """
        return await self.dashboard_repository.get_dashboard_summary_logs(
            start_date, end_date, group_by
        )
