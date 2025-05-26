import unittest
from unittest.mock import MagicMock

from app.engine.socio_bee import SocioBeeStrategy


class TestSocioBeeStrategy(unittest.TestCase):
    def setUp(self):
        """
        Set up the SocioBeeStrategy with mocked dependencies.
        """
        self.strategy = SocioBeeStrategy()
        self.strategy.task_service = MagicMock()
        self.strategy.user_points_service = MagicMock()

    async def test_basic_engagement(self):
        """
        Test Case 1: If task_measurements_count < 2, it returns
          BasicEngagement.
        """
        self.strategy.user_points_service.count_measurements_by_external_task_id.return_value = (
            1
        )
        points, status = await self.strategy.calculate_points(
            "game_id", "task_id", "user_id"
        )

        self.assertEqual(points, 1)
        self.assertEqual(status, "BasicEngagement")

    async def test_performance_bonus(self):
        """
        Test Case 2.1: If user_avg_time_taken < all_avg_time_taken, it returns
          PerformanceBonus.
        """
        self.strategy.user_points_service.count_measurements_by_external_task_id.return_value = (
            3
        )
        self.strategy.user_points_service.get_user_task_measurements_count.return_value = (
            3
        )
        self.strategy.user_points_service.get_avg_time_between_tasks_by_user_and_game_task.return_value = (
            5
        )
        self.strategy.user_points_service.get_avg_time_between_tasks_for_all_users.return_value = (
            10
        )

        points, status = await self.strategy.calculate_points(
            "game_id", "task_id", "user_id"
        )

        self.assertEqual(points, 11)
        self.assertEqual(status, "PerformanceBonus")

    async def test_individual_over_global(self):
        """
        Test Case 4.1: If user_diff_time < all_avg_time_taken, it returns
          IndividualOverGlobal.
        """
        self.strategy.user_points_service.count_measurements_by_external_task_id.return_value = (
            3
        )
        self.strategy.user_points_service.get_user_task_measurements_count.return_value = (
            3
        )
        self.strategy.user_points_service.get_avg_time_between_tasks_by_user_and_game_task.return_value = (
            10
        )
        self.strategy.user_points_service.get_avg_time_between_tasks_for_all_users.return_value = (
            5
        )
        self.strategy.user_points_service.get_last_window_time_diff.return_value = 3
        self.strategy.user_points_service.get_new_last_window_time_diff.return_value = 5

        points, status = await self.strategy.calculate_points(
            "game_id", "task_id", "user_id"
        )

        self.assertEqual(points, 3)
        self.assertEqual(status, "IndividualOverGlobal")

    async def test_peak_performer_bonus(self):
        """
        Test Case 4.2: If user_diff_time < user_avg_time_taken, it returns
          PeakPerformerBonus.
        """
        self.strategy.user_points_service.count_measurements_by_external_task_id.return_value = (
            3
        )
        self.strategy.user_points_service.get_user_task_measurements_count.return_value = (
            3
        )
        self.strategy.user_points_service.get_avg_time_between_tasks_by_user_and_game_task.return_value = (
            10
        )
        self.strategy.user_points_service.get_avg_time_between_tasks_for_all_users.return_value = (
            5
        )
        self.strategy.user_points_service.get_last_window_time_diff.return_value = 2
        self.strategy.user_points_service.get_new_last_window_time_diff.return_value = 7

        points, status = await self.strategy.calculate_points(
            "game_id", "task_id", "user_id"
        )

        self.assertEqual(status, "PeakPerformerBonus")
        self.assertEqual(points, 15)

    async def test_global_advantage_adjustment(self):
        """
        Test Case 4.3: If user_diff_time > user_avg_time_taken, it returns
          GlobalAdvantageAdjustment.
        """
        self.strategy.user_points_service.count_measurements_by_external_task_id.return_value = (
            3
        )
        self.strategy.user_points_service.get_user_task_measurements_count.return_value = (
            3
        )
        self.strategy.user_points_service.get_avg_time_between_tasks_by_user_and_game_task.return_value = (
            10
        )
        self.strategy.user_points_service.get_avg_time_between_tasks_for_all_users.return_value = (
            7
        )
        self.strategy.user_points_service.get_last_window_time_diff.return_value = 1
        self.strategy.user_points_service.get_new_last_window_time_diff.return_value = (
            12
        )

        points, status = await self.strategy.calculate_points(
            "game_id", "task_id", "user_id"
        )

        self.assertEqual(status, "GlobalAdvantageAdjustment")
        self.assertEqual(points, 7)

    async def test_individual_adjustment(self):
        """
        Test Case 4.4: If user_diff_time < 0, it returns IndividualAdjustment.
        """
        self.strategy.user_points_service.count_measurements_by_external_task_id.return_value = (
            3
        )
        self.strategy.user_points_service.get_user_task_measurements_count.return_value = (
            3
        )
        self.strategy.user_points_service.get_avg_time_between_tasks_by_user_and_game_task.return_value = (
            10
        )
        self.strategy.user_points_service.get_avg_time_between_tasks_for_all_users.return_value = (
            5
        )
        self.strategy.user_points_service.get_last_window_time_diff.return_value = 5
        self.strategy.user_points_service.get_new_last_window_time_diff.return_value = 3

        points, status = await self.strategy.calculate_points(
            "game_id", "task_id", "user_id"
        )

        self.assertEqual(points, 8)
        self.assertEqual(status, "IndividualAdjustment")

    async def test_default_case(self):
        """
        Test Default Case: If none of the conditions are met, it returns the
          default points.
        """
        self.strategy.user_points_service.count_measurements_by_external_task_id.return_value = (
            3
        )
        self.strategy.user_points_service.get_user_task_measurements_count.return_value = (
            2
        )

        points, status = await self.strategy.calculate_points(
            "game_id", "task_id", "user_id"
        )

        self.assertEqual(points, 1)
        self.assertEqual(status, "default")


if __name__ == "__main__":
    unittest.main()
