"""
### Gamification Scenarios, Points Allocation Table with Tags, Required Variables, and Condition Checks

#### Basic Engagement Scenario

| Case/Subcase | Conditions                                                              | Points Awarded                                        | Tag               | Required Variables            | Condition Check |
| ------------ | ----------------------------------------------------------------------- | ----------------------------------------------------- | ----------------- | ----------------------------- | --------------- |
| Case 1       | First/second measurement without any prior users having 2 measurements. | Basic initial points (`defaut_points_task_campaign`). | `BasicEngagement` | `defaut_points_task_campaign` | None Required   |

#### Comparative Performance Scenarios

| Case/Subcase | Conditions                                               | Points Awarded                                                                     | Tag                  | Required Variables                                                            | Condition Check                               |
| ------------ | -------------------------------------------------------- | ---------------------------------------------------------------------------------- | -------------------- | ----------------------------------------------------------------------------- | --------------------------------------------- |
| Case 2.1     | Second measurement with time taken > global calculation. | Fixed points or bonus/penalty based on the difference from the global calculation. | `PerformancePenalty` | `defaut_points_task_campaign`, `tiempo_tardado_ultima_task`, `Calculo_global` | `tiempo_tardado_ultima_task > Calculo_global` |
| Case 2.2     | Second measurement with time taken < global calculation. | Base points + bonus.                                                               | `PerformanceBonus`   | `defaut_points_task_campaign`, `tiempo_tardado_ultima_task`, `Calculo_global` | `tiempo_tardado_ultima_task < Calculo_global` |

#### Individual Improvement Scenario

| Case/Subcase | Conditions                                                  | Points Awarded        | Tag                    | Required Variables                                                                | Condition Check                                    |
| ------------ | ----------------------------------------------------------- | --------------------- | ---------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------- |
| Case 3       | Comparison with individual calculation (greater or lesser). | Base + bonus/penalty. | `IndividualAdjustment` | `defaut_points_task_campaign`, `tiempo_tardado_ultima_task`, `calculo_individual` | `tiempo_tardado_ultima_task <> calculo_individual` |

#### Advanced Gamification Strategies

| Case/Subcase | Conditions                                           | Points Awarded                                                                          | Tag                         | Required Variables                                                                                  | Condition Check                                                                                  |
| ------------ | ---------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Case 4.1     | Individual improvement but below the global average. | Adjusted points based on individual improvement without penalty for global performance. | `IndividualOverGlobal`      | `defaut_points_task_campaign`, `tiempo_tardado_ultima_task`, `calculo_individual`, `Calculo_global` | `tiempo_tardado_ultima_task < calculo_individual && tiempo_tardado_ultima_task > Calculo_global` |
| Case 4.2     | Individual worsening and below the global average.   | Default points.                                                                         | `NeedForMotivation`         | `defaut_points_task_campaign`, `tiempo_tardado_ultima_task`, `calculo_individual`, `Calculo_global` | `tiempo_tardado_ultima_task > calculo_individual && tiempo_tardado_ultima_task > Calculo_global` |
| Case 4.3     | Individual improvement and above the global average. | Significantly increased points.                                                         | `PeakPerformerBonus`        | `defaut_points_task_campaign`, `tiempo_tardado_ultima_task`, `calculo_individual`, `Calculo_global` | `tiempo_tardado_ultima_task < calculo_individual && tiempo_tardado_ultima_task < Calculo_global` |
| Case 4.4     | Individual worsening, but above the global average.  | Adjusted points based on global performance.                                            | `GlobalAdvantageAdjustment` | `defaut_points_task_campaign`, `tiempo_tardado_ultima_task`, `calculo_individual`, `Calculo_global` | `tiempo_tardado_ultima_task > calculo_individual && tiempo_tardado_ultima_task < Calculo_global` |

Gamification System Decision Tree
.
├── Is it the user's first or second measurement in the campaign?
│ ├── Yes
│ │ └── Use Case 1: `BasicEngagement`
│ └── No
│ └── Is this the user's second measurement?
│ ├── Yes
│ │ └── Is the time taken for the last task greater than the global calculation?
│ │ ├── Yes
│ │ │ └── Use Case 2.1: `PerformancePenalty`
│ │ └── No
│ │ └── Use Case 2.2: `PerformanceBonus`
│ └── No (It's a subsequent measurement)
│ └── Is the time taken for the last task greater or less than the individual calculation?
│ ├── Greater or equal
│ │ └── Evaluate against both, individual and global calculations
│ │ ├── If time is less than the individual calculation AND greater than the global calculation
│ │ │ └── Use Case 4.1: `IndividualOverGlobal`
│ │ ├── If time is greater than both, individual and global calculations
│ │ │ └── Use Case 4.2: `NeedForMotivation`
│ │ ├── If time is less than both, individual and global calculations
│ │ │ └── Use Case 4.3: `PeakPerformerBonus`
│ │ └── If time is greater than the individual calculation but less than the global calculation
│ │ └── Use Case 4.4: `GlobalAdvantageAdjustment`
│ └── Less
│ └── Use Case 3: `IndividualAdjustment`

# EXAMPLE

| Function Name                        | Description                                                                                     | Points Awarded |
| ------------------------------------ | ----------------------------------------------------------------------------------------------- | -------------- |
| `basic_engagement_points`            | Fixed number of points for a user's initial actions within the gamification system.             | 1              |
| `performance_penalty_points`         | Points deducted as a penalty for performance below a certain threshold.                         | -5             |
| `performance_bonus_points`           | Additional points awarded for performance above a certain threshold.                            | 10             |
| `individual_over_global_points`      | Additional points for users who have improved their performance compared to their own history.  | 5              |
| `need_for_motivation_points`         | Small point incentive for users underperforming both individually and globally.                 | 2              |
| `peak_performer_bonus_points`        | Bonus points for users exceeding both their individual performance and the global average.      | 15             |
| `global_advantage_adjustment_points` | Additional points for users above the global average but with decreased individual performance. | 7              |
| `individual_adjustment_points`       | Points awarded for users who have improved their individual performance.                        | 8              |


"""

from app.engine.base_strategy import BaseStrategy


class EnhancedGamificationStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            strategy_name="EnhancedGamificationStrategy",
            strategy_description="A more advanced gamification strategy with"
                                 "additional points and penalties.",
            strategy_name_slug="enhanced_gamification",
            strategy_version="0.0.2",
            variable_basic_points=1,
            variable_bonus_points=1
        )

        self.basic_engagement_points = 1
        self.performance_penalty_points = -5
        self.performance_bonus_points = 10
        self.individual_over_global_points = 5
        self.need_for_motivation_points = 2
        self.peak_performer_bonus_points = 15
        self.global_advantage_adjustment_points = 7
        self.individual_adjustment_points = 8

    def calculate_points(self, variables, case=None):
        # ACA WIP
        pass
