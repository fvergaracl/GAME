""" """

from app.core.container import Container
from app.engine.base_strategy import BaseStrategy
from app.engine.strategy_registry import register_strategy


@register_strategy(id="constantEffortStrategy", version="0.0.1")
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
        self.user_points_analytics_service = Container.user_points_analytics_service()

        self.default_points_task_campaign = 1
        self.variable_basic_points = 1
        self.variable_bonus_points = 10
        self.variable_constant_effort_interval_minutes = 5
        self.variable_max_points = 100

    async def calculate_points(
        self, externalGameId, externalTaskId, externalUserId, data=None
    ):
        """
        Award points for sustained effort within a rolling time window.

        If the user already has measurements in the last
        ``variable_constant_effort_interval_minutes`` minutes, the award scales
        with how consistent they have been (``ConstantEffortReward``);
        otherwise a flat basic point is granted (``BasicReward``).

        Args:
            externalGameId: External identifier of the game.
            externalTaskId: External identifier of the task.
            externalUserId: External identifier of the user.
            data: Optional event payload (unused by this strategy).

        Returns:
            tuple[int, str]: The points to award and the case name describing
            which branch produced them.
        """
        task_measurements_count = await self.user_points_analytics_service.get_user_task_measurements_count_the_last_seconds(
            externalTaskId,
            externalUserId,
            self.variable_constant_effort_interval_minutes * 60,
        )
        self.debug_print(f"task_measurements_count: {task_measurements_count}")
        if task_measurements_count > 0:
            points = self._calculate_points_from_consistency(
                task_measurements_count + 1
            )
            return points, "ConstantEffortReward"
        return 1, "BasicReward"

    def _calculate_points_from_consistency(self, consistent_effort_count):
        """
        Map a consistent-effort streak to a bounded point value.

        Args:
            consistent_effort_count: Number of consecutive in-window
                measurements (including the current one).

        Returns:
            int: Points normalized against ``variable_max_points`` and clamped
            to the range ``[1, variable_max_points]``.
        """
        normalized_points = (consistent_effort_count / self.variable_max_points) * 100
        return min(max(int(normalized_points), 1), self.variable_max_points)
