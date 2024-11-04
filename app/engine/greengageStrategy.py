"""
# noqa
https://dreampuf.github.io/GraphvizOnline/?compressed=CYSw5gTghgDgFgAgOIIN4CgFYdAdga1AgF4AVAIQG5NsatcB7YAUwQG0BnOWZ4gIwYAPADQIOAFwCeAG14AzENNnBRCpQGMG0hiWng44yFEkBdatgTNgYVmzkNc4jiABevAIwAGM3QSzJzLjAbNJQfMzSxABEALYAXAgAsiC4AK7izBwIADq4CAAiAAoJ%2BcxyUKnS4giFDClOOXkI5MXNDqlZtfVZjTUtCYXMEBwOUNJtaZ11jlm5BYWkAKIlZRVVNdMNpCAxrIuhMBxWvQDC%2BcQnDDEwsgBWIMBQwAXMAG4RDDC7jqeLF1c3Zj3R7PRaCG51cRQcQgBynRL-a53B5PJJQXBQGzfapzE6kRGA4Go0gMKHSKKqRTSTTaEgBJQMADukGYgRM6F8EigEGqITCEWiAGUoTyKWJuDBeBE9IdmJSNFodMQ9GADEZTOZsOo4Mx1PgQHJPOxQuFIrFiJ4oj4LNrdfq5AAZKASLqOADqzvcyVw5DKOmYfNN0VCEgQME2WQgzEZ3JYzwAFFCOPgAJQIAA8CHcCBiKStvlteo6Q24HCjmggwF99ijAElcKRnfhAwKogBVI4QBClnC6nTPcI11iJpsp-M2nV6g0AJnL-ayLbNxa73HeCAAfAhp72K8AOAB%2BBDxpBQXZj61ayf2g3bXa1jhIKPQoakbi4JDaPhjACCADUUIu0SCBuyCfmMCB-igx6nsw56alghbXnIt7MPej7MM%2BECvuigzDKM0iQca-JmsBm64SMGLjIR0Fnla8EIL4-iBMA06AVEJxjOolTQrCeS4viCBnAgADUgmLCJgmJL08wrAouDHCkYjiNAGRgJICAAFRHniAD0XieGmvRFEsCDEPMCAAOs5r0LSmfMJmifGxmLDp04pnMhS2WZzkSU5CwuQALGmYpqNSiokKQqQQAAjqkdRHOyHI2s6zDuAA%2BtmbEcUcWYAHTZn5Y6iFwPDEDA3JjLI2hGDE8phbSyr6FI0pMheCEpel25ZSleXbn5rlFeKpXldASgfDVdU0kqKoGPS2iMm1CDqClXUmq22WsH1RSWVug0lZKZUVWN1XQLVCChVNuhNXNrX0ctRwAMxEUG7E9U98YtHtEq8CNlXjadk3hY1qrNQyC13SlAUZc9609QF%2BVHp5hRfcNR1VQwE3nVSl3A7NLXgwWkNpatxHRBtCDw1t-kowdv3HRjANYwqDUzaD83Wkl2BcjyCAALSbohBqeAWV5C3zAtXsupZzpW1b%2BvWjbJjDZoAJqZOOl52lLzoy1Wfp1g2Tb80touOs64iuuIHocF6KRy1GyvRGrHAawhptOi6mzW7bPr68wxv3alxNsc7rtu3aBoexbXuet69v%2BwLHUZWxAByDBhyLWudtLfay37CtG4nRwky9adh4LhriybEdyLOud7o7URl%2ByE413Xu5ZAHK2N83mdTrXuudxLNc3jsqEPk%2BGRYW%2BH4MF%2BBH-o3oct5r-ej3eE8YVP2HvmBC8oF3j1L%2BrK-h2vyFj2hk8vjPe%2BEQHpvr%2BP6GYTv5H4YRqfp6f1fnyhV9bxvjhIYFEfyL0PswKGmU1qqxPn3JC-9N6vzfO-Si98i6QOJj3b%2BHIAC%2B6BcFAA
"""

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

        if hasattr(self, "variable_bonus_points"):
            del self.variable_bonus_points
        if hasattr(self, "variable_basic_points"):
            del self.variable_basic_points

        self.task_service = Container.task_service()
        self.user_points_service = Container.user_points_service()

        self.debug = True

        self.variable_default_points = 10
        self.variable_minutes_to_check = 1  # minutes if is case 1.1 or 1.2
        self.time_ranges = [0, 1, 15, 30, 60, float("inf")]

        self.variable_complexity = {
            "None": 0,
            "Very_low": 20,
            "Low": 40,
            "Normal": 60,
            "High": 80,
            "Very_high": 100,
        }

        self.variable_dimension_complexity = {
            "development": 0,
            "exploitation": 0,
            "management": 0,
        }

    def get_DPTE(self, points, minutes: int = 0):
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
                return points * self.time_ranges[i - 1]
        return points * self.time_ranges[-2]

    def get_BP(self, points: int = 0, minutes: int = 0):
        """
        Returns the Bonus Points (BP) based on the number of minutes elapsed.

        Args:
            minutes (int): The number of minutes elapsed.

        Returns:
            int: The Bonus Points (BP).

        """
        DPTE = self.get_DPTE(points, minutes)
        response = DPTE + (DPTE / 2)
        return response

    def get_PBP(self, points: int = 0, minutes: int = 0):
        """
        Returns the Personal Bonus Points (PBP) based on the number of minutes
          elapsed.

        Args:
            minutes (int): The number of minutes elapsed.

        Returns:
            int: The Personal Bonus Points (PBP).

        """
        DPTE = self.get_DPTE(points, minutes)
        response = DPTE + (DPTE / 4)
        return response

    def generate_logic_graph(self, format="png"):
        dot = Digraph(comment="Points Calculation Logic", format=format)

        # Set overall graph attributes
        dot.attr(rankdir="TB")
        dot.attr("node", shape="box", style="filled", fillcolor="lightgray")
        dot.attr("edge", fontsize="10")

        # Add Legend nodes
        dot.node(
            "leyend",
            label="m: Minutes \nDP: Default Points \nBP: Bonus Points \nPBP: Personal Bonus Points \nDPTE: Default Points Time Elapsed \DC=Development Complexity [0,100] \nEC=Exploitation Complexity [0,100] \nMC=Management Complexity [0,100] \nTC=Total Complexity [100,300]",
            fillcolor="yellowgreen",
        )

        # Add Nodes
        dot.node("start", "Start", shape="ellipse", fillcolor="lightgray")
        dot.node(
            "leyend2",
            label="Calculation \TC= DC + EC + MC \nDP: Defined in strategy * (CT/100) \nDPTE = DP × m \nBP = DPTE + (DPTE/2) \nPBP = DPTE + (DPTE/4)",
            fillcolor="Turquoise",
        )
        dot.node("checkif0", "m=0")
        dot.node("checkuserhasrecordBeforeInTask", "User has record before (task)")
        dot.node("checkifLastPointWas1MinBefore", "last points rewarded (task) < 1 min")
        dot.node("checkif2records", "user have > 2 records? (Game)")
        dot.node("checkififTimeIsGreaterThanGlobalAVG", "m > Global AVG (Game)")
        dot.node("checkififTimeIsGreaterThanPersonalAVG", "m > Personal AVG (Game)")

        # Case Nodes
        dot.node(
            "case1_1", "Case 1.1 (DP)", shape="parallelogram", fillcolor="lightyellow"
        )
        dot.node(
            "case1_2", "Case 1.2 (DP/2)", shape="parallelogram", fillcolor="lightyellow"
        )
        dot.node(
            "case2", "Case 2 (DP × 2)", shape="parallelogram", fillcolor="lightyellow"
        )
        dot.node("case3", "Case 3 (BP)", shape="parallelogram", fillcolor="lightyellow")
        dot.node(
            "case4_1", "Case 4.1 (PBP)", shape="parallelogram", fillcolor="lightyellow"
        )
        dot.node(
            "case4_2", "Case 4.2 (DPTE)", shape="parallelogram", fillcolor="lightyellow"
        )

        # Add Edges
        dot.edge("start", "checkif0")
        dot.edge("checkif0", "checkuserhasrecordBeforeInTask", label="Yes")
        dot.edge(
            "checkuserhasrecordBeforeInTask",
            "checkifLastPointWas1MinBefore",
            label="Yes",
        )
        dot.edge("checkifLastPointWas1MinBefore", "case1_2", label="Yes")
        dot.edge("checkifLastPointWas1MinBefore", "case1_1", label="No")
        dot.edge("checkuserhasrecordBeforeInTask", "case2", label="No")
        dot.edge("checkif0", "checkif2records", label="No")
        dot.edge("checkif2records", "case2", label="No")
        dot.edge("checkif2records", "checkififTimeIsGreaterThanGlobalAVG", label="Yes")
        dot.edge("checkififTimeIsGreaterThanGlobalAVG", "case3", label="Yes")
        dot.edge(
            "checkififTimeIsGreaterThanGlobalAVG",
            "checkififTimeIsGreaterThanPersonalAVG",
            label="No",
        )
        dot.edge("checkififTimeIsGreaterThanPersonalAVG", "case4_1", label="Yes")
        dot.edge("checkififTimeIsGreaterThanPersonalAVG", "case4_2", label="No")

        return dot

    def calculate_points(self, externalGameId, externalTaskId, externalUserId, data):
        minutes = data.get("minutes", None)
        if minutes is None:
            return (-1, 'The "minutes" field is required into the data')
        if not isinstance(minutes, int):
            return (-1, "The minutes must be a number equal or greater than 0")

        task_params = self.task_service.get_task_params_by_externalTaskId(
            externalTaskId
        )
        self.variable_dimension_complexity = {
            "development": 0,
            "exploitation": 0,
            "management": 0,
        }
        if task_params:
            for task_param in task_params:
                if task_param.key == "development":
                    self.variable_dimension_complexity["development"] = task_param.value
                if task_param.key == "exploitation":
                    self.variable_dimension_complexity["exploitation"] = (
                        task_param.value
                    )
                if task_param.key == "management":
                    self.variable_dimension_complexity["management"] = task_param.value

        points_to_award = self.variable_default_points

        user_has_record_before = (
            self.user_points_service.user_has_record_before_in_externalTaskId_last_min(
                externalTaskId, externalUserId, self.variable_minutes_to_check
            )
        )
        if minutes == 0:
            if not user_has_record_before:
                return (points_to_award, "Case 1.1 (DP)")
            return (points_to_award / 2, "Case 1.2 (DP/2)")

        count_personal_records_in_game = (
            self.user_points_service.count_personal_records_by_external_game_id(
                externalGameId, externalUserId
            )
        )
        if count_personal_records_in_game < 2:
            return (points_to_award * 2, "Case 2 (DP x 2)")

        global_avg_game = self.user_points_service.get_global_avg_by_external_game_id(
            externalGameId
        )
        if minutes > global_avg_game:
            return (self.get_BP(points_to_award, minutes), "Case 3 (BP)")

        personal_avg_game = (
            self.user_points_service.get_personal_avg_by_external_game_id(
                externalGameId, externalUserId
            )
        )
        if minutes > personal_avg_game:
            return (self.get_PBP(points_to_award, minutes), "Case 4.1 (PBP)")
        return (self.get_DPTE(points_to_award, minutes), "Case 4.2 (DPTE)")
