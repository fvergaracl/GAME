import unittest
from unittest.mock import AsyncMock

from app.services.user_points_analytics_service import UserPointsAnalyticsService


class TestUserPointsAnalyticsService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repo = AsyncMock()
        self.service = UserPointsAnalyticsService(user_points_repository=self.repo)

    async def test_repository_passthrough_methods_delegate_and_return(self):
        self.repo.count_measurements_by_external_task_id.return_value = 5
        self.repo.get_user_task_measurements_count.return_value = 2
        self.repo.get_user_task_measurements_count_the_last_seconds.return_value = 1
        self.repo.get_avg_time_between_tasks_by_user_and_game_task.return_value = 10.5
        self.repo.get_avg_time_between_tasks_for_all_users.return_value = 8.2
        self.repo.get_last_window_time_diff.return_value = 4
        self.repo.get_new_last_window_time_diff.return_value = 6
        self.repo.get_user_task_measurements.return_value = [{"minutes": 5}]
        self.repo.count_personal_records_by_external_game_id.return_value = 7
        self.repo.user_has_record_before_in_externalTaskId_last_min.return_value = True
        self.repo.get_global_avg_by_external_game_id.return_value = 12.3
        self.repo.get_personal_avg_by_external_game_id.return_value = 9.9

        self.assertEqual(
            await self.service.count_measurements_by_external_task_id("task"), 5
        )
        self.assertEqual(
            await self.service.get_user_task_measurements_count("task", "user"), 2
        )
        self.assertEqual(
            await self.service.get_user_task_measurements_count_the_last_seconds(
                "task", "user", 60
            ),
            1,
        )
        self.assertEqual(
            await self.service.get_avg_time_between_tasks_by_user_and_game_task(
                "game", "task", "user"
            ),
            10.5,
        )
        self.assertEqual(
            await self.service.get_avg_time_between_tasks_for_all_users("game", "task"),
            8.2,
        )
        self.assertEqual(
            await self.service.get_last_window_time_diff("task", "user"), 4
        )
        self.assertEqual(
            await self.service.get_new_last_window_time_diff("task", "user", "game"),
            6,
        )
        self.assertEqual(
            await self.service.get_user_task_measurements("task", "user"),
            [{"minutes": 5}],
        )
        self.assertEqual(
            await self.service.count_personal_records_by_external_game_id(
                "game", "user"
            ),
            7,
        )
        self.assertTrue(
            await self.service.user_has_record_before_in_externalTaskId_last_min(
                "task", "user", 5
            )
        )
        self.assertEqual(
            await self.service.get_global_avg_by_external_game_id("game"), 12.3
        )
        self.assertEqual(
            await self.service.get_personal_avg_by_external_game_id("game", "user"),
            9.9,
        )


if __name__ == "__main__":
    unittest.main()
