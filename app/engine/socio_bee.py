"""
# noqa
https://dreampuf.github.io/GraphvizOnline/#digraph%20G%20%7B%0A%20%20%20%20rankdir%3DTB%3B%0A%20%20%20%20%0A%20%20%20%20node%20%5Bshape%3Dbox%2C%20style%3Dfilled%2C%20fillcolor%3Dlightgray%5D%3B%0A%20%20%20%20edge%20%5Bfontsize%3D10%5D%3B%0A%0A%20%20%20%20start%20%5Blabel%3D%22Start%22%2C%20shape%3Dellipse%2C%20fillcolor%3Dlightgray%5D%3B%0A%20%20%20%20is1or2%20%5Blabel%3D%221st%20or%202nd%20Measure%3F%22%5D%3B%0A%20%20%20%20is2nd%20%5Blabel%3D%222nd%20Measure%3F%22%5D%3B%0A%20%20%20%20subseq%20%5Blabel%3D%22Subsequent%3F%22%5D%3B%0A%20%20%20%20evalTime%20%5Blabel%3D%22Eval%20Time%22%5D%3B%0A%20%20%20%20%0A%20%20%20%20case1%20%5Blabel%3D%22Case%201%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20case2_1%20%5Blabel%3D%22Case%202.1%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20case2_2%20%5Blabel%3D%22Case%202.2%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20case3%20%5Blabel%3D%22Case%203%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20case4_1%20%5Blabel%3D%22Case%204.1%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20case4_2%20%5Blabel%3D%22Case%204.2%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20case4_3%20%5Blabel%3D%22Case%204.3%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20case4_4%20%5Blabel%3D%22Case%204.4%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20default%20%5Blabel%3D%22Default%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%0A%20%20%20%20start%20-%3E%20is1or2%0A%20%20%20%20is1or2%20-%3E%20case1%20%5Blabel%3D%22Yes%22%5D%0A%20%20%20%20is1or2%20-%3E%20is2nd%20%5Blabel%3D%22No%22%5D%0A%20%20%20%20is2nd%20-%3E%20case2_1%20%5Blabel%3D%22Yes%2C%20%3C%20Global%22%5D%0A%20%20%20%20is2nd%20-%3E%20case2_2%20%5Blabel%3D%22Yes%2C%20%3E%3D%20Global%22%5D%0A%20%20%20%20is2nd%20-%3E%20subseq%20%5Blabel%3D%22No%22%5D%0A%20%20%20%20subseq%20-%3E%20evalTime%0A%20%20%20%20evalTime%20-%3E%20case3%20%5Blabel%3D%22%5B%3C%20Indiv%5D%22%5D%0A%20%20%20%20evalTime%20-%3E%20case4_1%20%5Blabel%3D%22%5B%3C%20Indiv%2C%20%3E%20Global%5D%22%5D%0A%20%20%20%20evalTime%20-%3E%20case4_2%20%5Blabel%3D%22%5B%3E%20Both%20Avgs%5D%22%5D%0A%20%20%20%20evalTime%20-%3E%20case4_3%20%5Blabel%3D%22%5B%3C%20Both%20Avgs%5D%22%5D%0A%20%20%20%20evalTime%20-%3E%20case4_4%20%5Blabel%3D%22%5B%3E%20Indiv%2C%20%3C%3D%20Global%5D%22%5D%0A%20%20%20%20evalTime%20-%3E%20default%20%5Blabel%3D%22Else%22%5D%0A%7D%0A

"""

from app.core.container import Container
from app.engine.base_strategy import BaseStrategy


class SocioBeeStrategy(BaseStrategy):  # noqa
    def __init__(self):
        super().__init__(
            strategy_name="SOCIO_BEE",
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
        if task_measurements_count < 2:
            return (self.variable_basic_points, "BasicEngagement")
        user_task_measurements_count = (
            self.user_points_service.get_user_task_measurements_count(
                externalTaskId, externalUserId
            )
        )
        self.debug_print(
            f"user_task_measurements_count: {user_task_measurements_count}"
        )

        if user_task_measurements_count > 2:
            user_avg_time_taken = self.user_points_service.get_avg_time_between_tasks_by_user_and_game_task(  # noqa
                externalGameId, externalTaskId, externalUserId
            )
            self.debug_print(f"user_avg_time_taken: {user_avg_time_taken}")

            all_avg_time_taken = self.user_points_service.get_avg_time_between_tasks_for_all_users(  # noqa
                externalGameId, externalTaskId
            )
            self.debug_print(f"all_avg_time_taken: {all_avg_time_taken}")

            if user_avg_time_taken < all_avg_time_taken:

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
                f"user_last_window_time_diff: {user_last_window_time_diff}"
            )

            user_new_last_window_time_diff = (
                self.user_points_service.get_new_last_window_time_diff(
                    externalTaskId, externalUserId, externalGameId
                )
            )
            self.debug_print(
                f"user_new_last_window_time_diff: " f"{user_new_last_window_time_diff}"
            )

            user_diff_time = user_new_last_window_time_diff - user_last_window_time_diff
            self.debug_print(f"user_diff_time: {user_diff_time}")
            if user_diff_time > 0:
                if user_diff_time < all_avg_time_taken:
                    return (
                        self.variable_individual_over_global_points,
                        "IndividualOverGlobal",
                    )
                if user_diff_time < user_avg_time_taken:
                    return (
                        self.variable_peak_performer_bonus_points,
                        "PeakPerformerBonus",
                    )
                if user_diff_time > user_avg_time_taken:
                    return (
                        self.variable_global_advantage_adjustment_points,
                        "GlobalAdvantageAdjustment",
                    )
            if user_diff_time < 0:
                return (
                    self.variable_individual_adjustment_points,
                    "IndividualAdjustment",
                )
            return (self.default_points_task_campaign, "default")
        return (self.default_points_task_campaign, "default")
