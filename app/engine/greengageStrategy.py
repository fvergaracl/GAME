"""
# noqa
https://dreampuf.github.io/GraphvizOnline/#digraph%20G%20%7B%0A%20%20%20%20rankdir%3DTB%3B%0A%20%20%20%20%0A%20%20%20%20node%20%5Bshape%3Dbox%2C%20style%3Dfilled%2C%20fillcolor%3Dlightgray%5D%3B%0A%20%20%20%20edge%20%5Bfontsize%3D10%5D%3B%0A%20%20%20%20leyend%5Blabel%3D%22x%3AMinutes%20%5Cn%20DP%3A%20Default%20Points%20%5Cn%20%20BP%3A%20Bonus%20Points%20%20%5Cn%20PBP%3A%20Personal%20Bonus%20Points%20%5Cn%20DPTE%3A%20Default%20Points%20Time%20Elapsed%22%2C%20fillcolor%3Dyellowgreen%5D%0A%0A%20%20%20%20start%20%5Blabel%3D%22Start%22%2C%20shape%3Dellipse%2C%20fillcolor%3Dlightgray%5D%3B%0A%20%20%20%20checkif0%20%5Blabel%3D%22x%3D0%22%5D%3B%0A%20%20%20%20checkif2records%20%5Blabel%3D%22user%20have%20%3E%202%20records%3F%22%5D%3B%0A%20%20%20%20checkififTimeIsGreaterThanGlobalAVG%20%5Blabel%3D%22x%20%3E%20Global%20AVG%20(Game)%22%5D%3B%0A%20%20%20%20checkififTimeIsGreaterThanPersonalAVG%20%5Blabel%3D%22x%20%3E%20Personal%20AVG%20(Game)%22%5D%3B%0A%20%20%20%20%0A%0A%20%20%20%20case1%20%5Blabel%3D%22Case%201%20(DP)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20case2%20%5Blabel%3D%22Case%202%20(DP%20x%202)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20case3%20%5Blabel%3D%22Case%203%20(BP)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20case4_1%20%5Blabel%3D%22Case%204.1%20(PBP)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20case4_2%20%5Blabel%3D%22Case%204.2%20(DPTE)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%0A%0A%20%20%20%20start%20-%3E%20checkif0%0A%20%20%20%20checkif0%20-%3E%20case1%20%5Blabel%3D%22Yes%22%5D%0A%20%20%20%20checkif0%20-%3E%20checkif2records%20%5Blabel%3D%22No%22%5D%0A%20%20%20%20checkif2records%20-%3E%20case2%20%5Blabel%3D%22No%22%5D%0A%20%20%20%20checkif2records%20-%3E%20checkififTimeIsGreaterThanGlobalAVG%20%5Blabel%3D%22Yes%22%5D%0A%20%20%20%20checkififTimeIsGreaterThanGlobalAVG%20-%3E%20case3%20%5Blabel%3D%22Yes%22%5D%0A%20%20%20%20checkififTimeIsGreaterThanGlobalAVG%20-%3E%20checkififTimeIsGreaterThanPersonalAVG%20%5Blabel%3D%22No%22%5D%0A%20%20%20%20checkififTimeIsGreaterThanPersonalAVG%20-%3E%20case4_1%20%5Blabel%3D%22Yes%22%5D%0A%20%20%20%20checkififTimeIsGreaterThanPersonalAVG%20-%3E%20case4_2%20%5Blabel%3D%22No%22%5D%0A%0A%7D%0A%7D
"""

from app.core.container import Container
from app.engine.base_strategy import BaseStrategy


class GREENGAGEGamificationStrategy(BaseStrategy):  # noqa
    def __init__(self):
        super().__init__(
            strategy_name="GREENGAGEGamificationStrategy",
            strategy_description=(
                "A gamification strategy to reward users based on their time"
                " taken to complete a task."
            ),
            strategy_name_slug="greengage_gamification",
            strategy_version="0.0.1",
        )
        self.task_service = Container.task_service()
        self.user_points_service = Container.user_points_service()

        self.debug = True

        self.variable_default_points = 10
        self.time_ranges = [0, 1, 15, 30, 60, float("inf")]

    def get_DPTE(self, minutes: int = 0):
        """
        Returns the Default Points Time Elapsed (DPTE) based on the number of
          minutes elapsed.

        Args:
            minutes (int): The number of minutes elapsed.

        Returns:
            int: The Default Points Time Elapsed (DPTE).

        """

        for i, time_range in enumerate(self.time_ranges):
            if minutes < time_range:
                return self.variable_default_points * self.time_ranges[i]
        return -1

    def get_BP(self, minutes: int = 0):
        """
        Returns the Bonus Points (BP) based on the number of minutes elapsed.

        Args:
            minutes (int): The number of minutes elapsed.

        Returns:
            int: The Bonus Points (BP).

        """
        DPTE = self.get_DPTE(minutes)
        response = DPTE + (DPTE/2)
        return response

    def get_PBP(self, minutes: int = 0):
        """
        Returns the Personal Bonus Points (PBP) based on the number of minutes
          elapsed.

        Args:
            minutes (int): The number of minutes elapsed.

        Returns:
            int: The Personal Bonus Points (PBP).

        """
        DPTE = self.get_DPTE(minutes)
        response = DPTE + (DPTE/4)
        return response

    def calculate_points(
            self, externalGameId, externalTaskId, externalUserId, data
    ):
        

        minutes = data.get('minutes', None)
        if minutes is None:
            return (-1, "The \"minutes\" field is required into the data")
        if not isinstance(minutes, int):
            return (-1, "The minutes must be a number equal or greater than 0")
        
        if minutes == 0:
            return (self.variable_default_points, "Case 1 (DP)")


        # get count personal points in the game, should have "minutes" field in the data
        return (1, "default")
