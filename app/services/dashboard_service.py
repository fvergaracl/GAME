from app.repository.dashboard_repository import DashboardRepository
from app.services.base_service import BaseService

# from app.services.game_service import GameService
# from app.services.task_service import TaskService
# from app.services.user_service import UserService
# from app.services.user_points_service import UserPointsService
# from app.services.user_actions_service import UserActionsService

from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_repository import UserRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_actions_repository import UserActionsRepository


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
        user_points_repository: UserPointsRepository,
        user_actions_repository: UserActionsRepository,
    ):
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
        self.user_points_repository = user_points_repository
        self.user_actions_repository = user_actions_repository
        super().__init__(dashboard_repository)

    def get_dashboard_summary(self, start_date, end_date, group_by):
        """
        Retrieves the dashboard summary.

        Args:
            start_date: The start date for the summary.
            end_date: The end date for the summary.
            group_by: The group by for the summary (e.g. day, week, month).

        Returns:
            Dict[str, Any]: The dashboard summary.
        """
        return self.dashboard_repository.get_dashboard_summary(
            start_date, end_date, group_by
        )
