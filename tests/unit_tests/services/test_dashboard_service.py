import unittest
from unittest.mock import MagicMock

from app.services.dashboard_service import DashboardService


class TestDashboardService(unittest.TestCase):
    def setUp(self):
        self.dashboard_repository = MagicMock()
        self.game_repository = MagicMock()
        self.task_repository = MagicMock()
        self.user_repository = MagicMock()
        self.logs_repository = MagicMock()
        self.user_points_repository = MagicMock()
        self.user_actions_repository = MagicMock()

        self.service = DashboardService(
            dashboard_repository=self.dashboard_repository,
            game_repository=self.game_repository,
            task_repository=self.task_repository,
            user_repository=self.user_repository,
            logs_repository=self.logs_repository,
            user_points_repository=self.user_points_repository,
            user_actions_repository=self.user_actions_repository,
        )

    def test_init_sets_dependencies(self):
        self.assertIs(self.service.dashboard_repository, self.dashboard_repository)
        self.assertIs(self.service.game_repository, self.game_repository)
        self.assertIs(self.service.task_repository, self.task_repository)
        self.assertIs(self.service.user_repository, self.user_repository)
        self.assertIs(self.service.logs_repository, self.logs_repository)
        self.assertIs(self.service.user_points_repository, self.user_points_repository)
        self.assertIs(
            self.service.user_actions_repository, self.user_actions_repository
        )
        self.assertIs(self.service._repository, self.dashboard_repository)

    def test_get_dashboard_summary_delegates_to_repository(self):
        expected = {
            "new_users": [{"label": "2026-02-09", "count": 5}],
            "games_opened": [{"label": "2026-02-09", "count": 2}],
            "points_earned": [{"label": "2026-02-09", "count": 100}],
            "actions_performed": [{"label": "2026-02-09", "count": 40}],
        }
        self.dashboard_repository.get_dashboard_summary.return_value = expected

        result = self.service.get_dashboard_summary("2026-02-01", "2026-02-09", "day")

        self.assertEqual(result, expected)
        self.dashboard_repository.get_dashboard_summary.assert_called_once_with(
            "2026-02-01",
            "2026-02-09",
            "day",
        )

    def test_get_dashboard_summary_logs_delegates_to_repository(self):
        expected = {
            "info": [{"label": "2026-02", "count": 100}],
            "success": [{"label": "2026-02", "count": 70}],
            "error": [{"label": "2026-02", "count": 3}],
        }
        self.dashboard_repository.get_dashboard_summary_logs.return_value = expected

        result = self.service.get_dashboard_summary_logs(
            "2026-02-01",
            "2026-02-28",
            "month",
        )

        self.assertEqual(result, expected)
        self.dashboard_repository.get_dashboard_summary_logs.assert_called_once_with(
            "2026-02-01",
            "2026-02-28",
            "month",
        )


if __name__ == "__main__":
    unittest.main()
