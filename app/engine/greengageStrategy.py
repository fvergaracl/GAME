

from app.core.container import Container
from app.engine.base_strategy import BaseStrategy
from graphviz import Digraph


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
        self.variable_minutes_to_check = 1  # minutes if is case 1.1 or 1.2
        self.time_ranges = [0, 1, 15, 30, 60, float("inf")]

    def get_DPTE(self, minutes: int = 0):
        """
        Returns the Default Points Time Elapsed (DPTE) based on the number of
        minutes elapsed, using the floor of the time range.

        Args:
            minutes (int): The number of minutes elapsed.

        Returns:
            int: The Default Points Time Elapsed (DPTE).
        """
        for i, time_range in enumerate(self.time_ranges):
            if minutes < time_range:
                return self.variable_default_points * self.time_ranges[i - 1]
        return self.variable_default_points * self.time_ranges[-2]

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

    def generate_logic_graph(self, format="png"):
        dot = Digraph(comment="Points Calculation Logic", format=format)

        # Set overall graph attributes
        dot.attr(rankdir='TB')
        dot.attr('node', shape='box', style='filled', fillcolor='lightgray')
        dot.attr('edge', fontsize='10')

        # Add Legend nodes
        dot.node('leyend', label='m: Minutes \nDP: Default Points \nBP: Bonus Points \nPBP: Personal Bonus Points \nDPTE: Default Points Time Elapsed', fillcolor='yellowgreen')
        dot.node('leyend2', label='Calculation \nDP: Defined in strategy \nDPTE = DP × m \nBP = DPTE + (DPTE/2) \nPBP = DPTE + (DPTE/4)', fillcolor='Turquoise')

        # Add Nodes
        dot.node('start', 'Start', shape='ellipse', fillcolor='lightgray')
        dot.node('checkif0', 'm=0')
        dot.node('checkuserhasrecordBeforeInTask',
                 'User has record before (task)')
        dot.node('checkifLastPointWas1MinBefore',
                 'last points rewarded (task) < 1 min')
        dot.node('checkif2records', 'user have > 2 records? (Game)')
        dot.node('checkififTimeIsGreaterThanGlobalAVG',
                 'x > Global AVG (Game)')
        dot.node('checkififTimeIsGreaterThanPersonalAVG',
                 'x > Personal AVG (Game)')

        # Case Nodes
        dot.node('case1_1', 'Case 1.1 (DP)',
                 shape='parallelogram', fillcolor='lightyellow')
        dot.node('case1_2', 'Case 1.2 (DP/2)',
                 shape='parallelogram', fillcolor='lightyellow')
        dot.node('case2', 'Case 2 (DP × 2)',
                 shape='parallelogram', fillcolor='lightyellow')
        dot.node('case3', 'Case 3 (BP)', shape='parallelogram',
                 fillcolor='lightyellow')
        dot.node('case4_1', 'Case 4.1 (PBP)',
                 shape='parallelogram', fillcolor='lightyellow')
        dot.node('case4_2', 'Case 4.2 (DPTE)',
                 shape='parallelogram', fillcolor='lightyellow')

        # Add Edges
        dot.edge('start', 'checkif0')
        dot.edge('checkif0', 'checkuserhasrecordBeforeInTask', label='Yes')
        dot.edge('checkuserhasrecordBeforeInTask',
                 'checkifLastPointWas1MinBefore', label='Yes')
        dot.edge('checkifLastPointWas1MinBefore', 'case1_2', label='Yes')
        dot.edge('checkifLastPointWas1MinBefore', 'case1_1', label='No')
        dot.edge('checkuserhasrecordBeforeInTask', 'case2', label='No')
        dot.edge('checkif0', 'checkif2records', label='No')
        dot.edge('checkif2records', 'case2', label='No')
        dot.edge('checkif2records',
                 'checkififTimeIsGreaterThanGlobalAVG', label='Yes')
        dot.edge('checkififTimeIsGreaterThanGlobalAVG', 'case3', label='Yes')
        dot.edge('checkififTimeIsGreaterThanGlobalAVG',
                 'checkififTimeIsGreaterThanPersonalAVG', label='No')
        dot.edge('checkififTimeIsGreaterThanPersonalAVG',
                 'case4_1', label='Yes')
        dot.edge('checkififTimeIsGreaterThanPersonalAVG',
                 'case4_2', label='No')

        return dot

    def calculate_points(
            self, externalGameId, externalTaskId, externalUserId, data
    ):
        minutes = data.get('minutes', None)
        if minutes is None:
            return (-1, "The \"minutes\" field is required into the data")
        if not isinstance(minutes, int):
            return (-1, "The minutes must be a number equal or greater than 0")

        user_has_record_before = self.user_points_service.user_has_record_before_in_externalTaskId_last_min(
            externalTaskId, externalUserId, self.variable_minutes_to_check
        )
        if minutes == 0:
            if not user_has_record_before:
                return (self.variable_default_points, "Case 1.1 (DP)")
            return (self.variable_default_points / 2, "Case 1.2 (DP/2)")

        count_personal_records_in_game = self.user_points_service.count_personal_records_by_external_game_id(
            externalGameId, externalUserId
        )
        if (count_personal_records_in_game < 2):
            return (self.variable_default_points * 2, "Case 2 (DP x 2)")

        global_avg_game = self.user_points_service.get_global_avg_by_external_game_id(
            externalGameId
        )
        if minutes > global_avg_game:
            return (self.get_BP(minutes), "Case 3 (BP)")

        personal_avg_game = self.user_points_service.get_personal_avg_by_external_game_id(
            externalGameId, externalUserId
        )
        if minutes > personal_avg_game:
            return (self.get_PBP(minutes), "Case 4.1 (PBP)")
        return (self.get_DPTE(minutes), "Case 4.2 (DPTE)")
