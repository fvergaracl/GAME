"""
# noqa
https://dreampuf.github.io/GraphvizOnline/?engine=dot#digraph%20G%7B%0A%20%20%20%20rankdir%3DTB%3B%0A%20%20%20%20node%20%5Bshape%3Dbox%2C%20style%3Dfilled%2C%20fillcolor%3Dlightgray%5D%3B%0A%20%20%20%20edge%20%5Bfontsize%3D10%5D%3B%0A%20%20%20%20%0A%20%20%20%20leyend%5Blabel%3D%22BP%3A%20Base%20Points%20%5Cn%20DIM_BP%3A%20Base%20Points%20Reward%20%5Cn%20DIM_LBE%3A%20Location-Based%20Equity%20%5Cn%20DIM_TD%3A%20Time%20Diversity%20%5Cn%20DIM_PP%3A%20Personal%20Performance%20%5Cn%20DIM_S%3A%20Streak%20Bonus%22%2C%20fillcolor%3Dyellowgreen%5D%0A%20%20%20%20%0A%20%20%20%20start%20%5Blabel%3D%22Start%22%2C%20shape%3Dellipse%2C%20fillcolor%3Dlightgray%5D%3B%0A%20%20%20%20taskCompleted%20%5Blabel%3D%22Task%20Completed%3F%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignBP%20%5Blabel%3D%22Assign%20BP%20(DIM_BP)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20checkLBE%20%5Blabel%3D%22Evaluate%20DIM_LBE%5Cn(Geolocation%20Equity)%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignLBE%20%5Blabel%3D%22Assign%20BP%20*%200.5%20(if%20POI%20%3C%20Avg)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20checkTD%20%5Blabel%3D%22Evaluate%20DIM_TD%5Cn(Time%20Diversity)%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignTD%20%5Blabel%3D%22Assign%20BP%20*%20Coe_time%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20checkPP%20%5Blabel%3D%22Evaluate%20DIM_PP%5Cn(Personal%20Performance)%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignPP%20%5Blabel%3D%22Assign%20BP%20*%20(AVG_Time_Window%20-%20Last_Time_Window)%20%2F%20AVG_Time_Window%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20checkStreak%20%5Blabel%3D%22Evaluate%20DIM_S%5Cn(Consistency)%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignStreak%20%5Blabel%3D%22Assign%20BP%20*%20(2%5EDays_Consecutive%20%2F%207)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20totalPoints%20%5Blabel%3D%22Total%20Reward%20Calculation%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20start%20-%3E%20taskCompleted%3B%0A%20%20%20%20taskCompleted%20-%3E%20assignBP%20%5Blabel%3D%22Yes%22%5D%3B%0A%20%20%20%20taskCompleted%20-%3E%20totalPoints%20%5Blabel%3D%22No%22%2C%20style%3Ddashed%5D%3B%0A%20%20%20%20%0A%20%20%20%20assignBP%20-%3E%20checkLBE%3B%0A%20%20%20%20checkLBE%20-%3E%20assignLBE%20%5Blabel%3D%22POI%20%3C%20Avg%22%5D%3B%0A%20%20%20%20checkLBE%20-%3E%20checkTD%20%5Blabel%3D%22POI%20%3E%3D%20Avg%22%5D%3B%0A%20%20%20%20assignLBE%20-%3E%20checkTD%3B%0A%20%20%20%20%0A%20%20%20%20checkTD%20-%3E%20assignTD%20%5Blabel%3D%22Valid%20Time%20Slot%22%5D%3B%0A%20%20%20%20checkTD%20-%3E%20checkPP%20%5Blabel%3D%22Invalid%20Time%20Slot%22%5D%3B%0A%20%20%20%20assignTD%20-%3E%20checkPP%3B%0A%20%20%20%20%0A%20%20%20%20checkPP%20-%3E%20assignPP%20%5Blabel%3D%22Improved%20Response%20Time%22%5D%3B%0A%20%20%20%20checkPP%20-%3E%20checkStreak%20%5Blabel%3D%22No%20Improvement%22%5D%3B%0A%20%20%20%20assignPP%20-%3E%20checkStreak%3B%0A%20%20%20%20%0A%20%20%20%20checkStreak%20-%3E%20assignStreak%20%5Blabel%3D%22Maintained%20Streak%22%5D%3B%0A%20%20%20%20checkStreak%20-%3E%20totalPoints%20%5Blabel%3D%22No%20Streak%22%5D%3B%0A%20%20%20%20assignStreak%20-%3E%20totalPoints%3B%0A%7D
"""

import datetime
import hashlib
import random
from collections import defaultdict

import numpy as np
from graphviz import Digraph

from app.core.config import configs
from app.core.container import Container
from app.core.exceptions import InternalServerError
from app.engine.base_strategy import BaseStrategy
from app.schema.task_schema import SimulatedTaskPoints
from app.util.add_log import add_log
from app.util.calculate_hash_simulated_strategy import calculate_hash_simulated_strategy


def get_random_values_from_tasks(all_records):
    """
    Extracts all dimensions from the tasks and generates random values
    within the range of the minimum and maximum values found in the tasks.

    Args:
        all_records (list): A list of all tasks.

    Returns:
        dict: A dictionary containing random values for each dimension.
    """

    dimensions = ["DIM_BP", "DIM_LBE", "DIM_TD", "DIM_PP", "DIM_S"]

    values = {dim: [] for dim in dimensions}

    for record in all_records:
        # if have callbackData replace tasks with callbackData
        tasks = record.data.get("tasks", [])
        callbackData = record.data.get("callbackData", [])
        if len(callbackData) > 0:
            tasks = callbackData
        for task in tasks:
            for dim_dict in task.get("dimensions", []):
                for dim, value in dim_dict.items():
                    if dim in values:
                        values[dim].append(value)

    min_max_values = {
        dim: (np.min(vals), np.max(vals)) if vals else (0, 10)
        for dim, vals in values.items()
    }

    random_values = {
        dim: random.randint(min_val, max_val)
        for dim, (min_val, max_val) in min_max_values.items()
    }

    return random_values


def get_average_values_from_tasks(task, all_records):
    """
    Extracts all dimensions from the tasks and calculates
     the average integer values
    of the dimensions found in the tasks.

    Args:
        all_records (list): A list of all tasks.

    Returns:
        dict: A dictionary containing average integer values for each
         dimension.
    """

    dimensions = ["DIM_BP", "DIM_LBE", "DIM_TD", "DIM_PP", "DIM_S"]

    values = {dim: [] for dim in dimensions}

    for record in all_records:
        tasks = record.data.get("tasks", [])
        callbackData = record.data.get("callbackData", [])
        if callbackData:
            tasks = callbackData
        for task in tasks:
            for dim_dict in task.get("dimensions", []):
                for dim, value in dim_dict.items():
                    if dim in values:
                        values[dim].append(value)

    average_values = {
        dim: int(round(np.mean(vals))) if vals else 5 for dim, vals in values.items()
    }

    return average_values


def get_dynamic_values_from_tasks(
    task,
    list_ids_tasks,
    all_records,
    user,
    variable_basic_points,
    variable_lbe_multiplier,
):
    """
    Calculates dynamic values based on user participation in tasks.

    Args:
        task (object): The task object.
        list_ids_tasks (list): A list of task IDs with externalTaskId references.
        all_records (list): A list of all task participation records.
        user (object): The user object participating in tasks.
        variable_basic_points (int): The base points per participation.
        variable_lbe_multiplier (float): The location-based equity multiplier.

    Returns:
        dict: A dictionary containing calculated values for each dimension:
            - "DIM_BP": Base points adjusted for task uniqueness.
            - "DIM_LBE": Points adjusted for location-based equity.
            - "DIM_TD": Points based on temporal distribution of participation.
            - "DIM_PP": Points adjusted for participation periodicity.
            - "DIM_S": Streak-based points for continuous participation.
    """
    all_records = all_records.all()
    poi_external_id = task.externalTaskId.split("_")[1]
    user_id = user.id

    dim_bp_value = dim_lbe_value = dim_td_value = dim_pp_value = dim_s_value = 0

    #
    poi_task_map = defaultdict(set)
    for t in list_ids_tasks:
        poi_id = t["externalTaskId"].split("_")[1]
        poi_task_map[poi_id].add(t["id"])

    count_total_task_in_poi = len(poi_task_map.get(poi_external_id, []))
    count_unique_task_in_poi = len(
        {r.taskId for r in all_records if r.taskId in poi_task_map[poi_external_id]}
    )

    if count_total_task_in_poi > 0:
        dim_bp_value = variable_basic_points - int(
            round(
                variable_basic_points
                * (count_unique_task_in_poi / count_total_task_in_poi)
            )
        )

    #  DIM_LBE
    count_POI_records = sum(1 for r in all_records if r.taskId == task.id)
    avg_POI = len(all_records) / max(len(poi_task_map), 1)
    dim_lbe_value = (
        round(variable_basic_points * variable_lbe_multiplier)
        if avg_POI > 0 and count_POI_records < avg_POI
        else 0
    )

    #  DIM_TD
    time_slots = {
        "Late Night": (0, 6),
        "Morning": (6, 12),
        "Afternoon": (12, 18),
        "Evening": (18, 24),
    }
    slot_counts = defaultdict(int)

    for r in all_records:
        if r.taskId == task.id:
            record_hour = r.created_at.hour
            for slot, (start, end) in time_slots.items():
                if start <= record_hour < end:
                    slot_counts[slot] += 1
                    break

    current_slot = next(
        slot
        for slot, (start, end) in time_slots.items()
        if start <= datetime.datetime.utcnow().hour < end
    )
    total_other_slots = sum(slot_counts.values()) - slot_counts[current_slot]
    dim_td_value = (
        round(
            (1 - (slot_counts[current_slot] / total_other_slots))
            * variable_basic_points
        )
        if total_other_slots > 0
        else variable_basic_points
    )

    #  DIM_PP
    user_records = sorted(
        [r.created_at for r in all_records if r.userId == user_id])
    time_diffs = [
        (user_records[i] - user_records[i - 1]).total_seconds() / 60
        for i in range(1, len(user_records))
    ]

    avg_time_window = np.mean(time_diffs) if time_diffs else 0
    last_time_window = (
        (
            datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
            - user_records[-1]
        ).total_seconds()
        / 60
        if user_records
        else 0
    )

    alpha = (
        min(0.5, max(0.1, 1 - (last_time_window / avg_time_window)))
        if avg_time_window > 0
        else 0.3
    )
    smoothed_factor = (
        alpha * (avg_time_window - last_time_window) +
        (1 - alpha) * avg_time_window
        if avg_time_window > 0
        else 0
    )
    dim_pp_value = int(
        round(
            (max(0, smoothed_factor / avg_time_window) * variable_basic_points)
            if avg_time_window > 0
            else 0
        )
    )

    #  DIM_S
    unique_days = sorted(
        {r.created_at.date() for r in all_records if r.userId == user_id}
    )
    consecutive_days = sum(
        1
        for i in range(len(unique_days) - 1, -1, -1)
        if unique_days[i]
        >= (datetime.datetime.utcnow().date() - datetime.timedelta(days=i))
    )
    dim_s_value = round(variable_basic_points * (2 ** (consecutive_days / 5)))

    return {
        "DIM_BP": dim_bp_value,
        "DIM_LBE": dim_lbe_value,
        "DIM_TD": dim_td_value,
        "DIM_PP": dim_pp_value,
        "DIM_S": dim_s_value,
    }


def assign_random_scores(min_value: int, max_value: int):
    return {
        "DIM_BP": random.randint(min_value, max_value),
        "DIM_TD": random.randint(min_value, max_value),
        "DIM_LBE": random.randint(min_value, max_value),
        "DIM_PP": random.randint(min_value, max_value),
        "DIM_S": random.randint(min_value, max_value),
    }


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
        self.game_service = Container.game_service()
        self.user_points_service = Container.user_points_service()
        self.user_service = Container.user_service()
        self.service_log = Container.logs_service()

        self.variable_basic_points = 10
        self.variable_lbe_multiplier = 0.5
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
        dot.node(
            "taskCompleted", "Task Completed?", shape="diamond", fillcolor="lightblue"
        )
        dot.node(
            "assignBP",
            "Assign BP (DIM_BP)",
            shape="parallelogram",
            fillcolor="lightyellow",
        )

        dot.node(
            "checkLBE",
            "Evaluate DIM_LBE\n(Geolocation Equity)",
            shape="diamond",
            fillcolor="lightblue",
        )
        dot.node(
            "assignLBE",
            "Assign BP * 0.5 (if POI < Avg)",
            shape="parallelogram",
            fillcolor="lightyellow",
        )

        dot.node(
            "checkTD",
            "Evaluate DIM_TD\n(Time Diversity)",
            shape="diamond",
            fillcolor="lightblue",
        )
        dot.node(
            "assignTD",
            "Assign BP * Coe_time",
            shape="parallelogram",
            fillcolor="lightyellow",
        )

        dot.node(
            "checkPP",
            "Evaluate DIM_PP\n(Personal Performance)",
            shape="diamond",
            fillcolor="lightblue",
        )
        dot.node(
            "assignPP",
            "Assign BP * (AVG_Time_Window - Last_Time_Window) / AVG_Time_Window",
            shape="parallelogram",
            fillcolor="lightyellow",
        )

        dot.node(
            "checkStreak",
            "Evaluate DIM_S\n(Consistency)",
            shape="diamond",
            fillcolor="lightblue",
        )
        dot.node(
            "assignStreak",
            "Assign BP * (2^Days_Consecutive / 7)",
            shape="parallelogram",
            fillcolor="lightyellow",
        )

        dot.node(
            "totalPoints",
            "Total Reward Calculation",
            shape="parallelogram",
            fillcolor="lightyellow",
        )

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
        return hashlib.sha256(
            (configs.SECRET_KEY + str(data_string)).encode("utf-8")
        ).hexdigest()

    def simulate_strategy(
        self,
        data_to_simulate: dict = None,
        userGroup: str = "dynamic",
        user_last_task: dict = None
    ):
        """
        Simulates a strategy execution to estimate the points a user would
        receive based on a given game strategy and task set, without
        actually assigning the points.

        Dimensions:
            - Task Diversity Base Points (DIM_BP)
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
            userGroup (str): The user group to simulate the strategy for.
              Could be ["random_range", "average_score", "dynamic_calculation"]
            user_last_task (dict, optional): The last task of the user.

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

        task_to_simulate = data_to_simulate.get("task")
        allTasks = data_to_simulate.get("allTasks")
        external_user_id = data_to_simulate.get("externalUserId")

        if not task_to_simulate or not allTasks or not external_user_id:
            return InternalServerError("Missing data to simulate the strategy")

        total_simulated_points = 0

        DIM_BP = 0
        DIM_LBE = 0
        DIM_TD = 0
        DIM_PP = 0
        DIM_S = 0
        expiration_date = datetime.datetime.now() + datetime.timedelta(
            minutes=self.variable_simulation_valid_until
        )
        expiration_date = expiration_date.replace(tzinfo=datetime.timezone.utc)
        externalTaskId_simulate = task_to_simulate.externalTaskId
        if (user_last_task is not None and (
            user_last_task.taskId == task_to_simulate.id
            and ((datetime.datetime.now(datetime.timezone.utc) -
                  user_last_task.created_at).total_seconds()) > 300  # 5 minutes
        )):
            return SimulatedTaskPoints(
                externalUserId=external_user_id,
                externalTaskId=str(externalTaskId_simulate),
                userGroup=userGroup,
                dimensions=[
                    {"DIM_BP": DIM_BP},
                    {"DIM_LBE": DIM_LBE},
                    {"DIM_TD": DIM_TD},
                    {"DIM_PP": DIM_PP},
                    {"DIM_S": DIM_S},
                ],
                totalSimulatedPoints=total_simulated_points,
                expirationDate=str(expiration_date),
            )
        # RANDOM_RAGE ########################################################

        list_ids_tasks = []
        list_ids_tasks_to_ask = []
        for task in allTasks:
            list_ids_tasks_to_ask.append(task.id)
            list_ids_tasks.append(
                {"id": task.id, "externalTaskId": task.externalTaskId}
            )

        all_records = self.user_points_service.get_all_point_of_tasks_list(
            list_ids_tasks_to_ask, withData=True
        )

        if userGroup == "random_range":
            random_calculated = get_random_values_from_tasks(all_records)

            DIM_BP = random_calculated.get("DIM_BP")
            DIM_LBE = random_calculated.get("DIM_LBE")
            DIM_TD = random_calculated.get("DIM_TD")
            DIM_PP = random_calculated.get("DIM_PP")
            DIM_S = random_calculated.get("DIM_S")

        # END RANDOM_RAGE ########################################################

        # AVERAGE_SCORE ########################################################
        if userGroup == "average_score":
            average_calculated = get_average_values_from_tasks(
                task, all_records)

            DIM_BP = average_calculated.get("DIM_BP")
            DIM_LBE = average_calculated.get("DIM_LBE")
            DIM_TD = average_calculated.get("DIM_TD")
            DIM_PP = average_calculated.get("DIM_PP")
            DIM_S = average_calculated.get("DIM_S")

        # END AVERAGE_SCORE ########################################################

        # DYNAMIC_CALCULATION ########################################################
        if userGroup == "dynamic_calculation":
            user = self.user_service.get_user_by_externalUserId(
                external_user_id)
            dynamic_calculated = get_dynamic_values_from_tasks(
                task_to_simulate,
                list_ids_tasks,
                all_records,
                user,
                self.variable_basic_points,
                self.variable_lbe_multiplier,
            )
            DIM_BP = dynamic_calculated.get("DIM_BP")
            DIM_LBE = dynamic_calculated.get("DIM_LBE")
            DIM_TD = dynamic_calculated.get("DIM_TD")
            DIM_PP = dynamic_calculated.get("DIM_PP")
            DIM_S = dynamic_calculated.get("DIM_S")
        # END DYNAMIC_CALCULATION ########################################################
        total_simulated_points = DIM_BP + DIM_LBE + DIM_TD + DIM_PP + DIM_S

        return SimulatedTaskPoints(
            externalUserId=external_user_id,
            externalTaskId=str(externalTaskId_simulate),
            userGroup=userGroup,
            dimensions=[
                {"DIM_BP": DIM_BP},
                {"DIM_LBE": DIM_LBE},
                {"DIM_TD": DIM_TD},
                {"DIM_PP": DIM_PP},
                {"DIM_S": DIM_S},
            ],
            totalSimulatedPoints=total_simulated_points,
            expirationDate=str(expiration_date),
        )

    def checkISExpired(self, expiration_date):
        """
        Check if the expiration date has passed.
        """
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        return expiration_date < now_utc

    async def calculate_points(
        self, externalGameId, externalTaskId, externalUserId, data
    ):
        """
        Calculate the points for the GREENCROWD gamification strategy.

        Args:
            externalGameId (str): The external game ID.
            externalTaskId (str): The external task ID.
            externalUserId (str): The external user ID.
            data (dict): The data containing the dimensions for the points
              calculation. With the following structure:
                {
                    "experimentGroup": str,
                    "simulationHash": str,
                    "dimensions": [
                        {
                            "DIM_BP": int,
                            "DIM_LBE": int,
                            "DIM_TD": int,
                            "DIM_PP": int,
                            "DIM_S": int
                        }...
                    ]
                }


        """
        case_name = "-"
        points = -1

        # destructuring data
        simulationHash = data.get("simulationHash", "")
        tasks = data.get("tasks", [])
        if (tasks == []):
            game = self.game_service.get_game_by_external_id(
                externalGameId)

            tasks_simulated, externalGameId = (
                await self.user_points_service.get_points_simulated_of_user_in_game(
                    game.id, externalUserId, assign_control_group=True
                )
            )
            callback_data = tasks_simulated
            simulationHash = calculate_hash_simulated_strategy(
                tasks_simulated, externalGameId, externalUserId
            )
            task = next(
                (
                    task
                    for task in tasks_simulated
                    if task.externalTaskId == externalTaskId
                ),
                None,
            )
        tasks_simulated = []
        for task in tasks:
            tasks_simulated.append(SimulatedTaskPoints(**task))
        tasks = tasks_simulated
        calculated_hash = calculate_hash_simulated_strategy(
            tasks, externalGameId, externalUserId
        )
        if calculated_hash != simulationHash:
            return points, "Invalid hash"

        isExpired = False
        # select externalTaskId from tasks where externalTaskId = taksId
        task = next(
            (task for task in tasks if str(
                task.externalTaskId) == str(externalTaskId)),
            None,
        )

        callback_data = None
        previous_points = self.user_points_service.get_points_of_simulated_task(
            externalTaskId, simulationHash
        )
        if previous_points:

            game = self.game_service.get_game_by_external_id(externalGameId)

            tasks_simulated, externalGameId = (
                await self.user_points_service.get_points_simulated_of_user_in_game(
                    game.id, externalUserId, assign_control_group=True
                )
            )
            simulationHash = calculate_hash_simulated_strategy(
                tasks_simulated, externalGameId, externalUserId
            )
            callback_data = tasks_simulated
            await add_log(
                "greencrowdStrategy",
                "INFO",
                "Simulating strategy for user because the points have expired",
                {
                    "externalUserId": externalUserId,
                    "externalGameId": externalGameId,
                    "tasks": tasks_simulated,
                    "simulationHash": simulationHash,
                },
                self.service_log,
                None,
                None,
            )
            task = next(
                (
                    task
                    for task in tasks_simulated
                    if task.externalTaskId == externalTaskId
                ),
                None,
            )

            case_name = "Valid Simulation - Origin: Used simulation"
        if task:
            isExpired = self.checkISExpired(
                datetime.datetime.strptime(
                    task.expirationDate, "%Y-%m-%d %H:%M:%S.%f%z"
                )
            )

            if isExpired:
                game = self.game_service.get_game_by_external_id(
                    externalGameId)

                tasks_simulated, externalGameId = (
                    await self.user_points_service.get_points_simulated_of_user_in_game(
                        game.id, externalUserId, assign_control_group=True
                    )
                )
                callback_data = tasks_simulated
                simulationHash = calculate_hash_simulated_strategy(
                    tasks_simulated, externalGameId, externalUserId
                )
                task = next(
                    (
                        task
                        for task in tasks_simulated
                        if task.externalTaskId == externalTaskId
                    ),
                    None,
                )
                if case_name == "-":
                    case_name = "Valid Simulation - Origin: Expired simulation"

            points = 0
            DIM_BP = task.dimensions[0].get("DIM_BP")
            DIM_LBE = task.dimensions[1].get("DIM_LBE")
            DIM_TD = task.dimensions[2].get("DIM_TD")
            DIM_PP = task.dimensions[3].get("DIM_PP")
            DIM_S = task.dimensions[4].get("DIM_S")

            print(
                {
                    "DIM_BP": DIM_BP,
                    "DIM_LBE": DIM_LBE,
                    "DIM_TD": DIM_TD,
                    "DIM_PP": DIM_PP,
                    "DIM_S": DIM_S,
                }
            )
            points = DIM_BP + DIM_LBE + DIM_TD + DIM_PP + DIM_S
            if case_name == "-":
                case_name = "Valid Simulation"

        return points, case_name, callback_data
