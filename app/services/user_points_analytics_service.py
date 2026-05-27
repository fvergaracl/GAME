"""
Analytics service for user points.

Aggregations, temporal queries and metrics over ``user_points`` records.
Extracted from ``UserPointsService`` so CRUD/write paths and analytic queries
have separate, focused services.

These methods are thin pass-throughs over ``UserPointsRepository`` analytics
queries; they are consumed primarily by strategy engines (``app/engine``) to
compute rewards based on historical user behaviour.
"""
from typing import Any

from app.repository.user_points_repository import UserPointsRepository
from app.services.base_service import BaseService


class UserPointsAnalyticsService(BaseService):
    def __init__(self, user_points_repository: UserPointsRepository) -> None:
        self.user_points_repository = user_points_repository
        super().__init__(user_points_repository)

    async def count_measurements_by_external_task_id(
        self, external_task_id
    ) -> Any:
        return await self.user_points_repository.count_measurements_by_external_task_id(
            external_task_id
        )

    async def get_user_task_measurements_count(
        self, externalTaskId, externalUserId
    ) -> Any:
        return await self.user_points_repository.get_user_task_measurements_count(
            externalTaskId, externalUserId
        )

    async def get_user_task_measurements_count_the_last_seconds(
        self, externalTaskId, externalUserId, seconds
    ) -> Any:
        return await self.user_points_repository.get_user_task_measurements_count_the_last_seconds(
            externalTaskId, externalUserId, seconds
        )

    async def get_avg_time_between_tasks_by_user_and_game_task(
        self, externalGameId, externalTaskId, externalUserId
    ) -> Any:
        return await self.user_points_repository.get_avg_time_between_tasks_by_user_and_game_task(  # noqa
            externalGameId, externalTaskId, externalUserId
        )

    async def get_avg_time_between_tasks_for_all_users(
        self, externalGameId, externalTaskId
    ) -> Any:
        return await self.user_points_repository.get_avg_time_between_tasks_for_all_users(  # noqa
            externalGameId, externalTaskId
        )

    async def get_last_window_time_diff(
        self, externalTaskId, externalUserId
    ) -> Any:
        return await self.user_points_repository.get_last_window_time_diff(
            externalTaskId, externalUserId
        )

    async def get_new_last_window_time_diff(
        self, externalTaskId, externalUserId, externalGameId
    ) -> Any:
        return await self.user_points_repository.get_new_last_window_time_diff(
            externalTaskId, externalUserId, externalGameId
        )

    async def get_user_task_measurements(
        self, externalTaskId, externalUserId
    ) -> Any:
        return await self.user_points_repository.get_user_task_measurements(
            externalTaskId, externalUserId
        )

    async def count_personal_records_by_external_game_id(
        self, external_game_id, externalUserId
    ) -> Any:
        """Count the number of records for a user in a game."""
        return await self.user_points_repository.count_personal_records_by_external_game_id(
            external_game_id, externalUserId
        )

    async def user_has_record_before_in_externalTaskId_last_min(
        self, externalTaskId, externalUserId, minutes
    ) -> Any:
        """Check if a user has a record in the task in the last `minutes` minutes."""
        return await self.user_points_repository.user_has_record_before_in_externalTaskId_last_min(
            externalTaskId, externalUserId, minutes
        )

    async def get_global_avg_by_external_game_id(self, external_game_id) -> Any:
        """
        Get the global average time rewarded. Ignores entries with 0 minutes.
        """
        return await self.user_points_repository.get_global_avg_by_external_game_id(
            external_game_id
        )

    async def get_personal_avg_by_external_game_id(
        self, external_game_id, externalUserId
    ) -> Any:
        """
        Get the personal average time rewarded. Ignores entries with 0 minutes.
        """
        return await self.user_points_repository.get_personal_avg_by_external_game_id(
            external_game_id, externalUserId
        )
