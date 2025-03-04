import unittest
from unittest.mock import MagicMock, patch

from app.model.games import Games
from app.model.user_actions import UserActions
from app.model.user_points import UserPoints
from app.model.users import Users
from app.repository.dashboard_repository import DashboardRepository


class TestDashboardRepository(unittest.TestCase):

    def setUp(self):
        self.session_factory = MagicMock()
        self.repository = DashboardRepository(
            session_factory=self.session_factory,
            model_games=Games,
            model_users=Users,
            model_user_points=UserPoints,
            model_user_actions=UserActions,
        )

    @patch.object(DashboardRepository, "_execute_query")
    def test_get_dashboard_summary_day_grouping(self, mock_execute_query):
        """
        Verify that the get_dashboard_summary method returns the expected
          summary when grouping by "day".

        The method should call _execute_query 4 times (once for each metric)
          and return a dictionary with the results for each metric.

        """

        mock_execute_query.side_effect = [
            [{"label": "2024-10-29", "count": 2}],
            [{"label": "2024-10-29", "count": 1}],
            [{"label": "2024-10-29", "count": 100}],
            [{"label": "2024-10-29", "count": 5}],
        ]

        result = self.repository.get_dashboard_summary(
            "2024-10-29", "2024-10-29", "day"
        )

        expected_result = {
            "new_users": [{"label": "2024-10-29", "count": 2}],
            "games_opened": [{"label": "2024-10-29", "count": 1}],
            "points_earned": [{"label": "2024-10-29", "count": 100}],
            "actions_performed": [{"label": "2024-10-29", "count": 5}],
        }

        self.assertEqual(result, expected_result)

        self.assertEqual(mock_execute_query.call_count, 4)

    @patch.object(DashboardRepository, "_execute_query")
    def test_get_dashboard_summary_month_grouping(self, mock_execute_query):
        """
        Verify that the get_dashboard_summary method returns the expected
          summary when grouping by "month".

        The method should call _execute_query 4 times (once for each metric)
          and return a dictionary with the results for each metric.
        """
        mock_execute_query.side_effect = [
            [{"label": "10", "count": 30}],
            [{"label": "10", "count": 15}],
            [{"label": "10", "count": 500}],
            [{"label": "10", "count": 25}],
        ]

        result = self.repository.get_dashboard_summary(
            "2024-10-01", "2024-10-31", "month"
        )

        expected_result = {
            "new_users": [{"label": "10", "count": 30}],
            "games_opened": [{"label": "10", "count": 15}],
            "points_earned": [{"label": "10", "count": 500}],
            "actions_performed": [{"label": "10", "count": 25}],
        }

        self.assertEqual(result, expected_result)

        self.assertEqual(mock_execute_query.call_count, 4)

    @patch.object(DashboardRepository, "_execute_query")
    def test_get_dashboard_summary_week_grouping(self, mock_execute_query):
        """
        Verify that the get_dashboard_summary method returns the expected
          summary when grouping by "week".

        The method should call _execute_query 4 times (once for each metric)
          and return a dictionary with the results for each metric.

        """
        mock_execute_query.side_effect = [
            [{"label": "week_1_10", "count": 15}],
            [{"label": "week_1_10", "count": 7}],
            [{"label": "week_1_10", "count": 300}],
            [{"label": "week_1_10", "count": 20}],
        ]

        result = self.repository.get_dashboard_summary(
            "2024-10-01", "2024-10-07", "week"
        )

        expected_result = {
            "new_users": [{"label": "week_1_10", "count": 15}],
            "games_opened": [{"label": "week_1_10", "count": 7}],
            "points_earned": [{"label": "week_1_10", "count": 300}],
            "actions_performed": [{"label": "week_1_10", "count": 20}],
        }

        self.assertEqual(result, expected_result)

        self.assertEqual(mock_execute_query.call_count, 4)

    @patch.object(DashboardRepository, "_execute_query")
    def test_get_dashboard_summary_no_data(self, mock_execute_query):
        """
        Verify that the get_dashboard_summary method returns the expected
          summary when there is no data.

        The method should call _execute_query 4 times (once for each metric)
          and return a dictionary with the results for each metric.

        """
        mock_execute_query.side_effect = [
            [],
            [],
            [],
            [],
        ]

        result = self.repository.get_dashboard_summary(
            "2024-12-01", "2024-12-31", "day"
        )

        expected_result = {
            "new_users": [],
            "games_opened": [],
            "points_earned": [],
            "actions_performed": [],
        }

        self.assertEqual(result, expected_result)
        self.assertEqual(mock_execute_query.call_count, 4)


if __name__ == "__main__":
    unittest.main()
