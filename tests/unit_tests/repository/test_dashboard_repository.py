import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.core.exceptions import BadRequestError
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

    def test_process_query_applies_start_end_and_group_by(self):
        class DummyCreatedAt:
            def __ge__(self, other):
                return ("ge", other)

            def __le__(self, other):
                return ("le", other)

        self.repository.model_users = SimpleNamespace(created_at=DummyCreatedAt())
        query = MagicMock()
        query.filter.return_value = query
        query.group_by.return_value = query

        result = self.repository.process_query(
            query,
            start_date="2026-01-01",
            end_date="2026-01-31",
            group_by_column="group_col",
        )

        self.assertIs(result, query)
        query.filter.assert_any_call(("ge", "2026-01-01"))
        query.filter.assert_any_call(("le", "2026-01-31"))
        query.group_by.assert_called_once_with("group_col")

    def test_process_query_without_filters_returns_same_query(self):
        query = MagicMock()

        result = self.repository.process_query(query)

        self.assertIs(result, query)
        query.filter.assert_not_called()
        query.group_by.assert_not_called()

    def test_get_group_by_column_invalid_value_raises_bad_request(self):
        with self.assertRaises(BadRequestError) as exc_info:
            self.repository._get_group_by_column(self.repository.model_users, "year")

        self.assertIn("Invalid group_by value", str(exc_info.exception.detail))

    def test_execute_query_formats_results(self):
        class FakeRow:
            def __init__(self, label, count):
                self._label = label
                self.count = count

            def __getitem__(self, index):
                if index == 0:
                    return self._label
                raise IndexError(index)

        session = MagicMock()
        context_manager = MagicMock()
        context_manager.__enter__.return_value = session
        context_manager.__exit__.return_value = False
        self.session_factory.return_value = context_manager

        base_query = MagicMock()
        processed_query = MagicMock()
        processed_query.all.return_value = [
            FakeRow("2026-01-01", 2),
            FakeRow("2026-01-02", 4),
        ]
        session.query.return_value = base_query

        aggregation_field = MagicMock()
        labeled_aggregation = MagicMock(name="count_expr")
        aggregation_field.label.return_value = labeled_aggregation

        with patch.object(
            self.repository, "process_query", return_value=processed_query
        ) as mock_process_query:
            result = self.repository._execute_query(
                model=self.repository.model_users,
                group_by_column="group_col",
                start_date="2026-01-01",
                end_date="2026-01-31",
                aggregation_field=aggregation_field,
            )

        aggregation_field.label.assert_called_once_with("count")
        session.query.assert_called_once_with("group_col", labeled_aggregation)
        mock_process_query.assert_called_once_with(
            base_query, "2026-01-01", "2026-01-31", "group_col"
        )
        self.assertEqual(
            result,
            [
                {"label": "2026-01-01", "count": 2},
                {"label": "2026-01-02", "count": 4},
            ],
        )

    @patch.object(DashboardRepository, "_execute_query")
    def test_get_dashboard_summary_logs(self, mock_execute_query):
        mock_execute_query.side_effect = [
            [{"label": "2026-01-01", "count": 10}],
            [{"label": "2026-01-01", "count": 7}],
            [{"label": "2026-01-01", "count": 2}],
        ]

        result = self.repository.get_dashboard_summary_logs(
            "2026-01-01", "2026-01-31", "day"
        )

        self.assertEqual(
            result,
            {
                "info": [{"label": "2026-01-01", "count": 10}],
                "success": [{"label": "2026-01-01", "count": 7}],
                "error": [{"label": "2026-01-01", "count": 2}],
            },
        )
        self.assertEqual(mock_execute_query.call_count, 3)


if __name__ == "__main__":
    unittest.main()
