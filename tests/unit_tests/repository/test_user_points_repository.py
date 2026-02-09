import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.model.tasks import Tasks
from app.model.user_points import UserPoints
from app.model.users import Users
from app.repository.base_repository import BaseRepository
from app.repository.user_points_repository import UserPointsRepository


class TestUserPointsRepository(unittest.TestCase):
    def _build_query(
        self,
        all_result=None,
        first_result=None,
        one_result=None,
        count_result=0,
        scalar_result=None,
        yield_result=None,
    ):
        query = MagicMock()
        query.join.return_value = query
        query.filter.return_value = query
        query.order_by.return_value = query
        query.group_by.return_value = query
        query.limit.return_value = query
        query.with_entities.return_value = query
        query.all.return_value = all_result
        query.first.return_value = first_result
        query.one.return_value = one_result
        query.count.return_value = count_result
        query.scalar.return_value = scalar_result
        query.yield_per.return_value = yield_result
        return query

    def _build_repo(self, query_or_queries):
        session = MagicMock()
        if isinstance(query_or_queries, list):
            session.query.side_effect = query_or_queries
        else:
            session.query.return_value = query_or_queries
        context_manager = MagicMock()
        context_manager.__enter__.return_value = session
        context_manager.__exit__.return_value = False
        session_factory = MagicMock(return_value=context_manager)
        repository = UserPointsRepository(session_factory=session_factory)
        return repository, session

    def test_init_sets_internal_repositories_and_model(self):
        query = self._build_query()
        repository, _ = self._build_repo(query)

        self.assertIs(repository.model, UserPoints)
        self.assertIsInstance(repository.task_repository, BaseRepository)
        self.assertIsInstance(repository.user_repository, BaseRepository)
        self.assertIs(repository.task_repository.model, Tasks)
        self.assertIs(repository.user_repository.model, Users)

    def test_get_first_user_points_in_external_task_id_by_user_id(self):
        expected = {"id": "first-point"}
        query = self._build_query(first_result=expected)
        repository, _ = self._build_repo(query)

        result = repository.get_first_user_points_in_external_task_id_by_user_id(
            "task-1", "user-1"
        )

        self.assertEqual(result, expected)

    def test_get_all_user_points_by_game_id(self):
        expected = [SimpleNamespace(externalTaskId="task-1", points=10)]
        query = self._build_query(all_result=expected)
        repository, _ = self._build_repo(query)

        result = repository.get_all_UserPoints_by_gameId("game-1")

        self.assertEqual(result, expected)

    def test_get_all_user_points_by_task_id(self):
        expected = [SimpleNamespace(externalUserId="user-1", points=5)]
        query = self._build_query(all_result=expected)
        repository, _ = self._build_repo(query)

        result = repository.get_all_UserPoints_by_taskId("task-1")

        self.assertEqual(result, expected)

    def test_get_all_user_points_by_task_id_with_details(self):
        expected = [
            SimpleNamespace(externalUserId="user-1", points=5, pointsData=[{"points": 5}])
        ]
        query = self._build_query(all_result=expected)
        repository, _ = self._build_repo(query)

        result = repository.get_all_UserPoints_by_taskId_with_details("task-1")

        self.assertEqual(result, expected)

    def test_get_points_and_users_by_task_id(self):
        expected = [SimpleNamespace(externalUserId="user-1", points=7)]
        query = self._build_query(all_result=expected)
        repository, _ = self._build_repo(query)

        result = repository.get_points_and_users_by_taskId("task-1")

        self.assertEqual(result, expected)

    def test_get_task_by_external_user_id(self):
        expected = [SimpleNamespace(id="task-1")]
        query = self._build_query(all_result=expected)
        repository, _ = self._build_repo(query)

        result = repository.get_task_by_externalUserId("user-1")

        self.assertEqual(result, expected)

    def test_get_task_and_sum_points_by_user_id(self):
        expected = [SimpleNamespace(externalTaskId="task-1", points=12)]
        query = self._build_query(all_result=expected)
        repository, _ = self._build_repo(query)

        result = repository.get_task_and_sum_points_by_userId("user-id-1")

        self.assertEqual(result, expected)

    def test_get_user_measurement_count(self):
        query = self._build_query(one_result=SimpleNamespace(measurement_count=8))
        repository, _ = self._build_repo(query)

        result = repository.get_user_measurement_count("user-id-1")

        self.assertEqual(result, 8)

    def test_get_time_taken_for_last_task(self):
        dt = datetime(2026, 2, 10, 10, 0, 0)
        query = self._build_query(one_result=SimpleNamespace(last_task_time=dt))
        repository, _ = self._build_repo(query)

        result = repository.get_time_taken_for_last_task("user-id-1")

        self.assertEqual(result, dt)

    def test_get_individual_calculation(self):
        query = self._build_query(one_result=SimpleNamespace(average_points=4.25))
        repository, _ = self._build_repo(query)

        result = repository.get_individual_calculation("user-id-1")

        self.assertEqual(result, 4.25)

    def test_get_global_calculation(self):
        query = self._build_query(one_result=SimpleNamespace(average_points=3.5))
        repository, _ = self._build_repo(query)

        result = repository.get_global_calculation()

        self.assertEqual(result, 3.5)

    def test_get_start_time_for_last_task(self):
        dt = datetime(2026, 2, 9, 9, 0, 0)
        query = self._build_query(one_result=SimpleNamespace(start_time=dt))
        repository, _ = self._build_repo(query)

        result = repository.get_start_time_for_last_task("user-id-1")

        self.assertEqual(result, dt)

    def test_count_measurements_by_external_task_id(self):
        query = self._build_query(one_result=SimpleNamespace(measurement_count=15))
        repository, _ = self._build_repo(query)

        result = repository.count_measurements_by_external_task_id("task-1")

        self.assertEqual(result, 15)

    def test_get_user_task_measurements(self):
        expected = [SimpleNamespace(timestamp=datetime(2026, 2, 10, 10, 0, 0))]
        query = self._build_query(all_result=expected)
        repository, _ = self._build_repo(query)

        result = repository.get_user_task_measurements("task-1", "user-1")

        self.assertEqual(result, expected)

    def test_get_user_task_measurements_count(self):
        query = self._build_query(one_result=SimpleNamespace(measurement_count=3))
        repository, _ = self._build_repo(query)

        result = repository.get_user_task_measurements_count("task-1", "user-1")

        self.assertEqual(result, 3)

    def test_get_user_task_measurements_count_the_last_seconds(self):
        query = self._build_query(one_result=SimpleNamespace(measurement_count=2))
        repository, _ = self._build_repo(query)

        result = repository.get_user_task_measurements_count_the_last_seconds(
            "task-1", "user-1", 60
        )

        self.assertEqual(result, 2)

    def test_get_avg_time_between_tasks_by_user_and_game_task_returns_minus_one_when_insufficient(self):
        query = self._build_query(all_result=[(datetime(2026, 2, 10, 10, 0, 0),)])
        repository, _ = self._build_repo(query)

        result = repository.get_avg_time_between_tasks_by_user_and_game_task(
            "game-1", "task-1", "user-1"
        )

        self.assertEqual(result, -1)

    def test_get_avg_time_between_tasks_by_user_and_game_task_returns_average(self):
        t1 = datetime(2026, 2, 10, 10, 0, 0)
        t2 = datetime(2026, 2, 10, 10, 0, 20)
        t3 = datetime(2026, 2, 10, 10, 0, 50)
        query = self._build_query(all_result=[(t1,), (t2,), (t3,)])
        repository, _ = self._build_repo(query)

        result = repository.get_avg_time_between_tasks_by_user_and_game_task(
            "game-1", "task-1", "user-1"
        )

        self.assertEqual(result, 25.0)

    def test_get_avg_time_between_tasks_for_all_users_returns_minus_one_when_insufficient(self):
        query = self._build_query(all_result=[(datetime(2026, 2, 10, 10, 0, 0),)])
        repository, _ = self._build_repo(query)

        result = repository.get_avg_time_between_tasks_for_all_users("game-1", "task-1")

        self.assertEqual(result, -1)

    def test_get_avg_time_between_tasks_for_all_users_returns_average(self):
        t1 = datetime(2026, 2, 10, 10, 0, 0)
        t2 = datetime(2026, 2, 10, 10, 0, 10)
        t3 = datetime(2026, 2, 10, 10, 0, 40)
        query = self._build_query(all_result=[(t1,), (t2,), (t3,)])
        repository, _ = self._build_repo(query)

        result = repository.get_avg_time_between_tasks_for_all_users("game-1", "task-1")

        self.assertEqual(result, 20.0)

    def test_get_last_window_time_diff_returns_zero_when_insufficient_points(self):
        query = self._build_query(all_result=[SimpleNamespace(created_at=datetime.now())])
        repository, _ = self._build_repo(query)

        result = repository.get_last_window_time_diff("task-1", "user-1")

        self.assertEqual(result, 0)

    def test_get_last_window_time_diff_returns_seconds(self):
        t_now = datetime(2026, 2, 10, 10, 1, 0)
        t_prev = datetime(2026, 2, 10, 10, 0, 0)
        query = self._build_query(
            all_result=[
                SimpleNamespace(created_at=t_now),
                SimpleNamespace(created_at=t_prev),
            ]
        )
        repository, _ = self._build_repo(query)

        result = repository.get_last_window_time_diff("task-1", "user-1")

        self.assertEqual(result, 60.0)

    def test_get_new_last_window_time_diff_returns_zero_when_no_last_point(self):
        query = self._build_query(first_result=None)
        repository, session = self._build_repo(query)

        result = repository.get_new_last_window_time_diff("task-1", "user-1", "game-1")

        self.assertEqual(result, 0)
        self.assertEqual(session.query.call_count, 1)

    def test_get_new_last_window_time_diff_handles_naive_datetimes(self):
        last_created_at = datetime(2026, 2, 10, 10, 0, 0)
        current_time = datetime(2026, 2, 10, 10, 1, 30)
        first_query = self._build_query(
            first_result=SimpleNamespace(created_at=last_created_at)
        )
        second_query = self._build_query(scalar_result=current_time)
        repository, session = self._build_repo([first_query, second_query])

        result = repository.get_new_last_window_time_diff("task-1", "user-1", "game-1")

        self.assertEqual(result, 90.0)
        self.assertEqual(session.query.call_count, 2)

    def test_get_new_last_window_time_diff_handles_aware_last_point(self):
        last_created_at = datetime(2026, 2, 10, 10, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2026, 2, 10, 10, 2, 0, tzinfo=timezone.utc)
        first_query = self._build_query(
            first_result=SimpleNamespace(created_at=last_created_at)
        )
        second_query = self._build_query(scalar_result=current_time)
        repository, _ = self._build_repo([first_query, second_query])

        result = repository.get_new_last_window_time_diff("task-1", "user-1", "game-1")

        self.assertEqual(result, 120.0)

    def test_count_personal_records_by_external_game_id(self):
        query = self._build_query(one_result=SimpleNamespace(record_count=11))
        repository, _ = self._build_repo(query)

        result = repository.count_personal_records_by_external_game_id("game-1", "user-1")

        self.assertEqual(result, 11)

    def test_user_has_record_before_in_external_task_id_last_min_true(self):
        query = self._build_query(count_result=2)
        repository, _ = self._build_repo(query)

        result = repository.user_has_record_before_in_externalTaskId_last_min(
            "task-1", "user-1", 5
        )

        self.assertTrue(result)

    def test_user_has_record_before_in_external_task_id_last_min_false(self):
        query = self._build_query(count_result=0)
        repository, _ = self._build_repo(query)

        result = repository.user_has_record_before_in_externalTaskId_last_min(
            "task-1", "user-1", 5
        )

        self.assertFalse(result)

    def test_get_global_avg_by_external_game_id_returns_value(self):
        query = self._build_query(one_result=SimpleNamespace(average_minutes=6.4))
        repository, _ = self._build_repo(query)

        result = repository.get_global_avg_by_external_game_id("game-1")

        self.assertEqual(result, 6.4)

    def test_get_global_avg_by_external_game_id_returns_minus_one_when_none(self):
        query = self._build_query(one_result=SimpleNamespace(average_minutes=None))
        repository, _ = self._build_repo(query)

        result = repository.get_global_avg_by_external_game_id("game-1")

        self.assertEqual(result, -1)

    def test_get_personal_avg_by_external_game_id_returns_value(self):
        query = self._build_query(one_result=SimpleNamespace(average_minutes=3.2))
        repository, _ = self._build_repo(query)

        result = repository.get_personal_avg_by_external_game_id("game-1", "user-1")

        self.assertEqual(result, 3.2)

    def test_get_personal_avg_by_external_game_id_returns_minus_one_when_none(self):
        query = self._build_query(one_result=SimpleNamespace(average_minutes=None))
        repository, _ = self._build_repo(query)

        result = repository.get_personal_avg_by_external_game_id("game-1", "user-1")

        self.assertEqual(result, -1)

    def test_get_points_of_simulated_task(self):
        expected = [SimpleNamespace(id="up-1"), SimpleNamespace(id="up-2")]
        query = self._build_query(all_result=expected)
        repository, _ = self._build_repo(query)

        result = repository.get_points_of_simulated_task("task-1", "hash-1")

        self.assertEqual(result, expected)

    def test_get_all_point_of_tasks_list_without_data_uses_with_entities(self):
        expected = [SimpleNamespace(id="up-1")]
        query = self._build_query(yield_result=expected)
        repository, _ = self._build_repo(query)

        result = repository.get_all_point_of_tasks_list(["task-1", "task-2"], withData=False)

        self.assertEqual(result, expected)
        query.with_entities.assert_called_once()
        query.yield_per.assert_called_once_with(1000)

    def test_get_all_point_of_tasks_list_with_data_skips_with_entities(self):
        expected = [SimpleNamespace(id="up-1", data={"k": "v"})]
        query = self._build_query(yield_result=expected)
        repository, _ = self._build_repo(query)

        result = repository.get_all_point_of_tasks_list(["task-1"], withData=True)

        self.assertEqual(result, expected)
        query.with_entities.assert_not_called()
        query.yield_per.assert_called_once_with(1000)

    def test_get_last_task_by_user_id(self):
        expected = SimpleNamespace(id="last-point")
        query = self._build_query(first_result=expected)
        repository, _ = self._build_repo(query)

        result = repository.get_last_task_by_userId("user-id-1")

        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
