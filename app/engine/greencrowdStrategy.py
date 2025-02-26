"""
# noqa
https://dreampuf.github.io/GraphvizOnline/?engine=dot#digraph%20G%7B%0A%20%20%20%20rankdir%3DTB%3B%0A%20%20%20%20node%20%5Bshape%3Dbox%2C%20style%3Dfilled%2C%20fillcolor%3Dlightgray%5D%3B%0A%20%20%20%20edge%20%5Bfontsize%3D10%5D%3B%0A%20%20%20%20%0A%20%20%20%20leyend%5Blabel%3D%22BP%3A%20Base%20Points%20%5Cn%20DIM_BP%3A%20Base%20Points%20Reward%20%5Cn%20DIM_LBE%3A%20Location-Based%20Equity%20%5Cn%20DIM_TD%3A%20Time%20Diversity%20%5Cn%20DIM_PP%3A%20Personal%20Performance%20%5Cn%20DIM_S%3A%20Streak%20Bonus%22%2C%20fillcolor%3Dyellowgreen%5D%0A%20%20%20%20%0A%20%20%20%20start%20%5Blabel%3D%22Start%22%2C%20shape%3Dellipse%2C%20fillcolor%3Dlightgray%5D%3B%0A%20%20%20%20taskCompleted%20%5Blabel%3D%22Task%20Completed%3F%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignBP%20%5Blabel%3D%22Assign%20BP%20(DIM_BP)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20checkLBE%20%5Blabel%3D%22Evaluate%20DIM_LBE%5Cn(Geolocation%20Equity)%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignLBE%20%5Blabel%3D%22Assign%20BP%20*%200.5%20(if%20POI%20%3C%20Avg)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20checkTD%20%5Blabel%3D%22Evaluate%20DIM_TD%5Cn(Time%20Diversity)%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignTD%20%5Blabel%3D%22Assign%20BP%20*%20Coe_time%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20checkPP%20%5Blabel%3D%22Evaluate%20DIM_PP%5Cn(Personal%20Performance)%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignPP%20%5Blabel%3D%22Assign%20BP%20*%20(AVG_Time_Window%20-%20Last_Time_Window)%20%2F%20AVG_Time_Window%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20checkStreak%20%5Blabel%3D%22Evaluate%20DIM_S%5Cn(Consistency)%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignStreak%20%5Blabel%3D%22Assign%20BP%20*%20(2%5EDays_Consecutive%20%2F%207)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20totalPoints%20%5Blabel%3D%22Total%20Reward%20Calculation%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20start%20-%3E%20taskCompleted%3B%0A%20%20%20%20taskCompleted%20-%3E%20assignBP%20%5Blabel%3D%22Yes%22%5D%3B%0A%20%20%20%20taskCompleted%20-%3E%20totalPoints%20%5Blabel%3D%22No%22%2C%20style%3Ddashed%5D%3B%0A%20%20%20%20%0A%20%20%20%20assignBP%20-%3E%20checkLBE%3B%0A%20%20%20%20checkLBE%20-%3E%20assignLBE%20%5Blabel%3D%22POI%20%3C%20Avg%22%5D%3B%0A%20%20%20%20checkLBE%20-%3E%20checkTD%20%5Blabel%3D%22POI%20%3E%3D%20Avg%22%5D%3B%0A%20%20%20%20assignLBE%20-%3E%20checkTD%3B%0A%20%20%20%20%0A%20%20%20%20checkTD%20-%3E%20assignTD%20%5Blabel%3D%22Valid%20Time%20Slot%22%5D%3B%0A%20%20%20%20checkTD%20-%3E%20checkPP%20%5Blabel%3D%22Invalid%20Time%20Slot%22%5D%3B%0A%20%20%20%20assignTD%20-%3E%20checkPP%3B%0A%20%20%20%20%0A%20%20%20%20checkPP%20-%3E%20assignPP%20%5Blabel%3D%22Improved%20Response%20Time%22%5D%3B%0A%20%20%20%20checkPP%20-%3E%20checkStreak%20%5Blabel%3D%22No%20Improvement%22%5D%3B%0A%20%20%20%20assignPP%20-%3E%20checkStreak%3B%0A%20%20%20%20%0A%20%20%20%20checkStreak%20-%3E%20assignStreak%20%5Blabel%3D%22Maintained%20Streak%22%5D%3B%0A%20%20%20%20checkStreak%20-%3E%20totalPoints%20%5Blabel%3D%22No%20Streak%22%5D%3B%0A%20%20%20%20assignStreak%20-%3E%20totalPoints%3B%0A%7D
"""

import datetime
import hashlib
from app.core.container import Container
from app.core.exceptions import InternalServerError
from app.engine.base_strategy import BaseStrategy
from app.schema.task_schema import SimulatedTaskPoints
from graphviz import Digraph


class GREENCROWDGamificationStrategy(BaseStrategy):  # noqa
    def __init__(self):
        super().__init__(
            strategy_name="greencrowdStrategy",
            strategy_description=(
                "A gamification strategy to reward users based on task completion, "
                "geolocation equity, time diversity, personal performance, and streak consistency."
            ),
            strategy_name_slug="greencrowdStrategy",
            strategy_version="1.0.0",
        )
        self.task_service = Container.task_service()
        self.user_points_service = Container.user_points_service()

        self.variable_basic_points = 10
        self.variable_simulation_valid_until = 15
        self.time_slots = [(0, 6), (6, 12), (12, 18), (18, 24)]

    def generate_logic_graph(self, format="png"):
        dot = Digraph(
            comment="GREENCROWD Points Calculation Logic", format=format)
        dot.attr("node", shape="box", style="filled", fillcolor="lightgray")
        dot.attr("edge", fontsize="10")

        # Add Legend nodes
        dot.node(
            "leyend",
            label="BP: Base Points \nDIM_BP: Base Points Reward \nDIM_LBE: Location-Based Equity \nDIM_TD: Time Diversity \nDIM_PP: Personal Performance \nDIM_S: Streak Bonus",
            fillcolor="yellowgreen",
        )

        # Add Nodes
        dot.node("start", "Start", shape="ellipse", fillcolor="lightgray")
        dot.node("taskCompleted", "Task Completed?",
                 shape="diamond", fillcolor="lightblue")
        dot.node("assignBP", "Assign BP (DIM_BP)",
                 shape="parallelogram", fillcolor="lightyellow")

        dot.node("checkLBE", "Evaluate DIM_LBE\n(Geolocation Equity)",
                 shape="diamond", fillcolor="lightblue")
        dot.node("assignLBE", "Assign BP * 0.5 (if POI < Avg)",
                 shape="parallelogram", fillcolor="lightyellow")

        dot.node("checkTD", "Evaluate DIM_TD\n(Time Diversity)",
                 shape="diamond", fillcolor="lightblue")
        dot.node("assignTD", "Assign BP * Coe_time",
                 shape="parallelogram", fillcolor="lightyellow")

        dot.node("checkPP", "Evaluate DIM_PP\n(Personal Performance)",
                 shape="diamond", fillcolor="lightblue")
        dot.node("assignPP", "Assign BP * (AVG_Time_Window - Last_Time_Window) / AVG_Time_Window",
                 shape="parallelogram", fillcolor="lightyellow")

        dot.node("checkStreak", "Evaluate DIM_S\n(Consistency)",
                 shape="diamond", fillcolor="lightblue")
        dot.node("assignStreak", "Assign BP * (2^Days_Consecutive / 7)",
                 shape="parallelogram", fillcolor="lightyellow")

        dot.node("totalPoints", "Total Reward Calculation",
                 shape="parallelogram", fillcolor="lightyellow")

        # Add Edges
        dot.edge("start", "taskCompleted")
        dot.edge("taskCompleted", "assignBP", label="Yes")
        dot.edge("taskCompleted", "totalPoints", label="No", style="dashed")

        dot.edge("assignBP", "checkLBE")
        dot.edge("checkLBE", "assignLBE", label="POI < Avg")
        dot.edge("checkLBE", "checkTD", label="POI >= Avg")
        dot.edge("assignLBE", "checkTD")

        dot.edge("checkTD", "assignTD", label="Valid Time Slot")
        dot.edge("checkTD", "checkPP", label="Invalid Time Slot")
        dot.edge("assignTD", "checkPP")

        dot.edge("checkPP", "assignPP", label="Improved Response Time")
        dot.edge("checkPP", "checkStreak", label="No Improvement")
        dot.edge("assignPP", "checkStreak")

        dot.edge("checkStreak", "assignStreak", label="Maintained Streak")
        dot.edge("checkStreak", "totalPoints", label="No Streak")
        dot.edge("assignStreak", "totalPoints")

        return dot

    def generate_hash(self, response_data):
        """
        Generate a hash for the response to ensure integrity.
        """
        data_string = str(response_data).encode("utf-8")
        return hashlib.sha256((self.secret_key + str(data_string)).encode("utf-8")).hexdigest()

    def simulate_strategy(self, data_to_simulate: dict = None, userGroup: str = "dynamic"):
        """
        Simulates a strategy execution to estimate the points a user would
        receive based on a given game strategy and task set, without
        actually assigning the points.

        Dimensions:
            - Task Diversity (DIM_TD)
            - Location-Based Equity (DIM_LBE)
            - Time Diversity (DIM_TD)
            - Personal Performance (DIM_PP)
            - Streak Bonus (DIM_S)

        Args:
            data_to_simulate (dict, optional): A dictionary containing the
            necessary data for simulating the strategy. Expected structure:

                {
                    "task": dict # Single task object,
                    "allTasks": list # List of all tasks,
                    "externalUserId": str   # The external ID of the user for
                    whom the simulation is run.
                }
            userGroup (str): The user group to simulate the strategy for. Could be "random" , "static" or "dynamic"

        Returns:
            list: A list of dictionaries containing the results of the strategy
            simulation.
            Structure:
            [
                {
                    "externalUserId": str,  # The external ID of the user.
                    "dimensions": list,     # A list of dictionaries
                    containing the points for each dimension.
                    "totalSimulatedPoints": int,  # The total estimated points.
                }
            ]
        """

        # destructuring data_to_simulate to get the necessary data
        task = data_to_simulate.get("task")
        allTasks = data_to_simulate.get("allTasks")
        external_user_id = data_to_simulate.get("externalUserId")

        # if not all necessary data is provided, return an error message
        if not task or not allTasks or not external_user_id:
            return InternalServerError("Missing data to simulate the strategy")

        # initialize the total points variable
        total_simulated_points = 0

        # - Task Diversity (DIM_TD)
        #             - Location-Based Equity (DIM_LBE)
        #             - Time Diversity (DIM_TD)
        #             - Personal Performance (DIM_PP)
        #             - Streak Bonus (DIM_S)
        DIM_TD = 0
        DIM_LBE = 0
        DIM_TD = 0
        DIM_PP = 0
        DIM_S = 0

        total_simulated_points = DIM_TD + DIM_LBE + DIM_TD + DIM_PP + DIM_S

        # expirationDate = datetime.datetime.now() + datetime.timedelta( minutes=self.variable_simulation_valid_until) but in UTC 0
        expiration_date = datetime.datetime.now() + datetime.timedelta(
            minutes=self.variable_simulation_valid_until)
        # expirationDate with Time zone
        expiration_date = expiration_date.replace(tzinfo=datetime.timezone.utc)

        return SimulatedTaskPoints(
            externalUserId=external_user_id,
            taksId=str(task.id),
            dimensions=[
                {"DIM_TD": DIM_TD},
                {"DIM_LBE": DIM_LBE},
                {"DIM_TD": DIM_TD},
                {"DIM_PP": DIM_PP},
                {"DIM_S": DIM_S},
            ],
            totalSimulatedPoints=total_simulated_points,
            expirationDate=str(expiration_date),
        )

    def calculate_points(self, task_completed, poi_samples, avg_poi_samples, time_slot_samples, total_samples, avg_time_window, last_time_window, streak_days):
        """
        Calculate the total points based on EquiQuest gamification strategy.

        The calculation is based on five reward dimensions:
        1. **Base Points (DIM_BP):** Assigned if the task is successfully
          completed.
        2. **Location-Based Equity (DIM_LBE):** Encourages sampling in
          underrepresented POIs by providing a bonus if the POI is below the average sample count.
        3. **Time Diversity (DIM_TD):** Rewards users for sampling in less
          covered time slots to ensure a balanced temporal distribution.
        4. **Personal Performance (DIM_PP):** Provides a bonus if the user
          completes the task faster than their personal average time.
        5. **Streak (DIM_S):** Encourages consistent participation by
          rewarding exponential bonuses for consecutive participation days.

        Args:
            task_completed (bool): Whether the task was completed successfully.
            poi_samples (int): The number of samples collected in the current
              POI.
            avg_poi_samples (int): The average number of samples across POIs.
            time_slot_samples (int): The number of samples collected in the
              current time slot.
            total_samples (int): The total number of samples collected in all
              time slots.
            avg_time_window (float): The user's average time window between
              task completions (in seconds).
            last_time_window (float): The time difference between the user's
              last two task completions (in seconds).
            streak_days (int): The number of consecutive days the user has participated.

        Returns:
            dict: A dictionary containing:
                - "total_points" (float): The total points awarded.
                - "breakdown" (dict): Detailed points earned for each
                  dimension.
                - "normalized" (dict): Percentage contribution of each
                  dimension to the total points.
                - "valid_until" (datetime): The date until which the points
                  are valid.
                - "hash" (str): A hash to verify data integrity.
            str: A message summarizing the calculation.
        """
        if not task_completed:
            response = {
                "total_points": 0,
                "breakdown": {},
                "normalized": {},
                "valid_until": None,
            }
            response["hash"] = self.generate_hash(response)
            return response, "Task not completed"

        breakdown = {}
        total_points = self.variable_basic_points  # DIM_BP
        breakdown["Base Points"] = self.variable_basic_points

        # DIM_LBE (Location-Based Equity)
        if poi_samples < avg_poi_samples:
            lbe_bonus = self.variable_basic_points * 0.5
            total_points += lbe_bonus
            breakdown["Location-Based Equity"] = lbe_bonus
        else:
            breakdown["Location-Based Equity"] = 0

        # DIM_TD (Time Diversity)
        coe_time = (total_samples - time_slot_samples) / \
            total_samples if total_samples else 1
        td_bonus = self.variable_basic_points * coe_time
        total_points += td_bonus
        breakdown["Time Diversity"] = td_bonus

        # DIM_PP (Personal Performance)
        if last_time_window < avg_time_window:
            pp_bonus = self.variable_basic_points * \
                (avg_time_window - last_time_window) / avg_time_window
            total_points += pp_bonus
            breakdown["Personal Performance"] = pp_bonus
        else:
            breakdown["Personal Performance"] = 0

        # DIM_S (Streak Bonus)
        streak_bonus = self.variable_basic_points * (2 ** (streak_days / 7))
        total_points += streak_bonus
        breakdown["Streak Bonus"] = streak_bonus

        # Normalize points contribution
        normalized = {key: (value / total_points) * 100 if total_points >
                      0 else 0 for key, value in breakdown.items()}
        valid_until = datetime.datetime.now(
        ) + datetime.timedelta(minutes=self.variable_valid_until_minutes)

        response = {
            "total_points": total_points,
            "breakdown": breakdown,
            "normalized": normalized,
            "valid_until": valid_until,
        }
        response["hash"] = self.generate_hash(response)

        return response, "Points Calculation Completed"
