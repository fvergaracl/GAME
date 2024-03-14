"""
# noqa
### Enhanced Gamification Scenarios, Points Allocation Table with Tags, Required Variables, and Condition Checks 

#### Basic Engagement Scenario

| Case/Subcase | Conditions                                                              | Points Awarded                                        | Tag               | Required Variables            | Condition Check |
| ------------ | ----------------------------------------------------------------------- | ----------------------------------------------------- | ----------------- | ----------------------------- | --------------- |
| Case 1       | First/second measurement without any prior users having 2 measurements. | variable_basic_points | `BasicEngagement` | `default_points_task_campaign` | None Required   |

#### Comparative Performance Scenarios

| Case/Subcase | Conditions                                               | Points Awarded          | Tag                | Required Variables                                                            | Condition Check                               |
| ------------ | -------------------------------------------------------- | ----------------------- | ------------------ | ----------------------------------------------------------------------------- | --------------------------------------------- |
| Case 2       | Second measurement with time taken < global calculation. | variable_basic_points + variable_bonus_points.    | `PerformanceBonus` | `default_points_task_campaign`, `tiempo_tardado_ultima_task`, `calculo_global` | `tiempo_tardado_ultima_task < calculo_global` |

#### Individual Improvement Scenario

| Case/Subcase | Conditions                                                  | Points Awarded        | Tag                    | Required Variables                                                                | Condition Check                                    |
| ------------ | ----------------------------------------------------------- | --------------------- | ---------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------- |
| Case 3       | Comparison with individual calculation (greater or lesser). | variable_individual_adjustment_points         | `IndividualAdjustment` | `default_points_task_campaign`, `tiempo_tardado_ultima_task`, `calculo_individual` | `tiempo_tardado_ultima_task <> calculo_individual` |

#### Advanced Gamification Strategies

| Case/Subcase | Conditions                                           | Points Awarded                                                                    | Tag                         | Required Variables                                                                                  | Condition Check                                                                                  |
| ------------ | ---------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Case 4.1     | Individual improvement but below the global average. | variable_individual_over_global_points | `IndividualOverGlobal`      | `default_points_task_campaign`, `tiempo_tardado_ultima_task`, `calculo_individual`, `calculo_global` | `tiempo_tardado_ultima_task < calculo_individual && tiempo_tardado_ultima_task > calculo_global` |
| Case 4.2     | Individual improvement and above the global average. | variable_peak_performer_bonus_points                                               | `PeakPerformerBonus`        | `default_points_task_campaign`, `tiempo_tardado_ultima_task`, `calculo_individual`, `calculo_global` | `tiempo_tardado_ultima_task < calculo_individual && tiempo_tardado_ultima_task < calculo_global` |
| Case 4.3     | Individual worsening, but above the global average.  | variable_global_advantage_adjustment_points                                  | `GlobalAdvantageAdjustment` | `default_points_task_campaign`, `tiempo_tardado_ultima_task`, `calculo_individual`, `calculo_global` | `tiempo_tardado_ultima_task > calculo_individual && tiempo_tardado_ultima_task < calculo_global` |
#### Consistent Performance Bonus

| Case/Subcase | Conditions                                                             | Points Awarded                  | Tag                  | Required Variables                                                                                        | Condition Check                                                                 |
| ------------ | ---------------------------------------------------------------------- | ------------------------------- | -------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Case 5       | User maintains or improves their performance for 3 consecutive tasks. | variable_consistent_performance_bonus_points | `ConsistentPerformance` | `default_points_task_campaign`, `tiempo_tardado_ultimas_tres_tasks`, `promedio_tiempo_tardado_tres_tasks_anteriores`, `promedio_tiempo_tardado_todos_usuarios_tres_tasks_anteriores` | `tiempo_tardado_ultimas_tres_tasks <= promedio_tiempo_tardado_tres_tasks_anteriores && tiempo_tardado_ultimas_tres_tasks < promedio_tiempo_tardado_todos_usuarios_tres_tasks_anteriores` |

Gamification System Decision Tree
.
├── Is it the user's first or second measurement in the task in general?
│ ├── Yes
│ │ └── Use Case 1: `BasicEngagement` | points = variable_basic_points
│ └── No
│ └── Is this the user's second measurement?
│ ├── Yes
│ │ └── Is the time taken for the last task less than the global calculation?
│ │ └── Yes
│ │ └── Use Case 2: `PerformanceBonus` | points = variable_basic_points + variable_bonus_points
│ └── No (It's a subsequent measurement)
│ └── Is the time taken for the last task greater or less than the individual calculation?
│ ├── Greater or equal
│ │ └── Evaluate against both, individual and global calculations
│ │ ├── If time is less than the individual calculation AND greater than the global calculation
│ │ │ └── Use Case 4.1: `IndividualOverGlobal` | points = variable_individual_over_global_points
│ │ ├── If time is less than both, individual and global calculations
│ │ │ └── Use Case 4.2: `PeakPerformerBonus` | points = variable_peak_performer_bonus_points
│ │ └── If time is greater than the individual calculation but less than the global calculation
│ │ └── Use Case 4.3: `GlobalAdvantageAdjustment` | points = variable_global_advantage_adjustment_points
│ └── Less
│ └── Use Case 3: `IndividualAdjustment` | points = variable_individual_adjustment_points

# EXAMPLE

| Function Name                        | Description                                                                                     | Points Awarded |
| ------------------------------------ | ----------------------------------------------------------------------------------------------- | -------------- |
| `basic_engagement_points`            | Fixed number of points for a user's initial actions within the gamification system.             | 1              |
| `performance_bonus_points`           | Additional points awarded for performance above a certain threshold.                            | 10             |
| `individual_over_global_points`      | Additional points for users who have improved their performance compared to their own history.  | 3              |
| `peak_performer_bonus_points`        | Bonus points for users exceeding both their individual performance and the global average.      | 15             |
| `global_advantage_adjustment_points` | Additional points for users above the global average but with decreased individual performance. | 7              |
| `individual_adjustment_points`       | Points awarded for users who have improved their individual performance.                        | 8              |
"""

from app.engine.base_strategy import BaseStrategy
from app.core.container import Container


class EnhancedGamificationStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            strategy_name="EnhancedGamificationStrategy",
            strategy_description="A more advanced gamification strategy with "
            "additional points and penalties.",
            strategy_name_slug="enhanced_gamification",
            strategy_version="0.0.2",
            variable_basic_points=1,
            variable_bonus_points=1,
        )
        self.task_service = Container.task_service()
        self.user_points_service = Container.user_points_service()

        self.debug = True

        self.default_points_task_campaign = 1
        self.variable_basic_points = 1
        self.variable_bonus_points = 10
        self.variable_individual_over_global_points = 3
        self.variable_peak_performer_bonus_points = 15
        self.variable_global_advantage_adjustment_points = 7
        self.variable_individual_adjustment_points = 8

    def calculate_points(self, externalGameId, externalTaskId, externalUserId):
        task_measurements_count = (
            self.user_points_service.count_measurements_by_external_task_id(
                externalTaskId
            )
        )
        self.debug_print(f"task_measurements_count: {task_measurements_count}")
        if (task_measurements_count < 2):
            return (
                self.variable_basic_points, "BasicEngagement"
            )
        user_task_measurements_count = (
            self.user_points_service.get_user_task_measurements_count(
                externalTaskId, externalUserId
            )
        )
        self.debug_print(
            f"user_task_measurements_count: {user_task_measurements_count}")

        if (user_task_measurements_count > 2):
            user_avg_time_taken = self.user_points_service.get_avg_time_between_tasks_by_user_and_game_task(  # noqa
                externalGameId, externalTaskId, externalUserId
            )
            self.debug_print(f"user_avg_time_taken: {user_avg_time_taken}")

            all_avg_time_taken = self.user_points_service.get_avg_time_between_tasks_for_all_users(
                externalGameId,
                externalTaskId
            )
            self.debug_print(f"all_avg_time_taken: {all_avg_time_taken}")

            if (user_avg_time_taken < all_avg_time_taken):

                points = self.variable_basic_points + self.variable_bonus_points
                return (
                    points,
                    "PerformanceBonus",
                )
            user_last_window_time_diff = (
                self.user_points_service.get_last_window_time_diff(
                    externalTaskId, externalUserId
                )
            )
            self.debug_print(
                f"user_last_window_time_diff: {user_last_window_time_diff}")

            user_new_last_window_time_diff = (
                self.user_points_service.get_new_last_window_time_diff(
                    externalTaskId, externalUserId, externalGameId
                )
            )
            self.debug_print(
                f"user_new_last_window_time_diff: {user_new_last_window_time_diff}"
            )

            user_diff_time = (
                user_new_last_window_time_diff - user_last_window_time_diff
            )
            self.debug_print(f"user_diff_time: {user_diff_time}")
            if (user_diff_time > 0):
                if (user_diff_time < all_avg_time_taken):
                    return (
                        self.variable_individual_over_global_points,
                        "IndividualOverGlobal"
                    )
                if (user_diff_time < user_avg_time_taken):
                    return (
                        self.variable_peak_performer_bonus_points,
                        "PeakPerformerBonus"
                    )
                if (user_diff_time > user_avg_time_taken):
                    return (
                        self.variable_global_advantage_adjustment_points,
                        "GlobalAdvantageAdjustment"
                    )
            if (user_diff_time < 0):
                return (
                    self.variable_individual_adjustment_points,
                    "IndividualAdjustment"
                )
            return (
                self.default_points_task_campaign,
                "default"
            )
        return (
            self.default_points_task_campaign,
            "default"
        )
