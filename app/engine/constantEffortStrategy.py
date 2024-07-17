"""

"""
from app.engine.base_strategy import BaseStrategy
from app.core.container import Container


class ConstantEffortStrategy(BaseStrategy):  # noqa
    def __init__(self):
        super().__init__(
            strategy_name="ConstantEffortStrategy",
            strategy_description="A strategy that rewards consistent effort over 5-minute intervals.",
            strategy_name_slug="constant_effort",
            strategy_version="0.0.1",
            variable_basic_points=1,
            variable_bonus_points=10,
        )
        self.task_service = Container.task_service()
        self.user_points_service = Container.user_points_service()

        self.debug = True

        self.default_points_task_campaign = 1
        self.variable_basic_points = 1
        self.variable_bonus_points = 10
        self.variable_constant_effort_interval_minutes = 5
        self.variable_max_points = 100

    def calculate_points(self, externalGameId, externalTaskId, externalUserId):
        task_measurements_count = self.user_points_service.count_measurements_by_external_task_id(
            externalTaskId)
        self.debug_print(f"task_measurements_count: {task_measurements_count}")

        user_task_measurements = self.user_points_service.get_user_task_measurements(
            externalTaskId, externalUserId)
        self.debug_print(f"user_task_measurements: {user_task_measurements}")

        if not user_task_measurements:
            return self.default_points_task_campaign, "default"

        consistent_effort_count = self._calculate_consistent_effort(
            user_task_measurements)
        self.debug_print(f"consistent_effort_count: {consistent_effort_count}")

        points = self._calculate_points_from_consistency(
            consistent_effort_count)
        self.debug_print(f"calculated points: {points}")

        return points, "ConstantEffortReward"

    def _calculate_consistent_effort(self, user_task_measurements):
        consistent_effort_count = 0
        previous_measurement_time = None

        for measurement in user_task_measurements:
            if previous_measurement_time is None:
                previous_measurement_time = measurement['timestamp']
                continue

            time_difference = measurement['timestamp'] - \
                previous_measurement_time
            time_difference_minutes = time_difference.total_seconds() / 60

            if time_difference_minutes <= self.variable_constant_effort_interval_minutes:
                consistent_effort_count += 1

            previous_measurement_time = measurement['timestamp']

        return consistent_effort_count

    def _calculate_points_from_consistency(self, consistent_effort_count):
        # Normalize consistent effort count to a scale of 1 to 100
        normalized_points = (consistent_effort_count /
                             self.variable_max_points) * 100
        return min(max(int(normalized_points), 1), self.variable_max_points)

    def debug_print(self, message):
        if self.debug:
            print(message)
