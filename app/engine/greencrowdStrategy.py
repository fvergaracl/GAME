"""
# noqa
https://dreampuf.github.io/GraphvizOnline/?engine=dot#digraph%20G%7B%0A%20%20%20%20rankdir%3DTB%3B%0A%20%20%20%20node%20%5Bshape%3Dbox%2C%20style%3Dfilled%2C%20fillcolor%3Dlightgray%5D%3B%0A%20%20%20%20edge%20%5Bfontsize%3D10%5D%3B%0A%20%20%20%20%0A%20%20%20%20leyend%5Blabel%3D%22BP%3A%20Base%20Points%20%5Cn%20DIM_BP%3A%20Base%20Points%20Reward%20%5Cn%20DIM_LBE%3A%20Location-Based%20Equity%20%5Cn%20DIM_TD%3A%20Time%20Diversity%20%5Cn%20DIM_PP%3A%20Personal%20Performance%20%5Cn%20DIM_S%3A%20Streak%20Bonus%22%2C%20fillcolor%3Dyellowgreen%5D%0A%20%20%20%20%0A%20%20%20%20start%20%5Blabel%3D%22Start%22%2C%20shape%3Dellipse%2C%20fillcolor%3Dlightgray%5D%3B%0A%20%20%20%20taskCompleted%20%5Blabel%3D%22Task%20Completed%3F%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignBP%20%5Blabel%3D%22Assign%20BP%20(DIM_BP)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20checkLBE%20%5Blabel%3D%22Evaluate%20DIM_LBE%5Cn(Geolocation%20Equity)%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignLBE%20%5Blabel%3D%22Assign%20BP%20*%200.5%20(if%20POI%20%3C%20Avg)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20checkTD%20%5Blabel%3D%22Evaluate%20DIM_TD%5Cn(Time%20Diversity)%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignTD%20%5Blabel%3D%22Assign%20BP%20*%20Coe_time%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20checkPP%20%5Blabel%3D%22Evaluate%20DIM_PP%5Cn(Personal%20Performance)%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignPP%20%5Blabel%3D%22Assign%20BP%20*%20(AVG_Time_Window%20-%20Last_Time_Window)%20%2F%20AVG_Time_Window%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20checkStreak%20%5Blabel%3D%22Evaluate%20DIM_S%5Cn(Consistency)%22%2C%20shape%3Ddiamond%2C%20fillcolor%3Dlightblue%5D%3B%0A%20%20%20%20assignStreak%20%5Blabel%3D%22Assign%20BP%20*%20(2%5EDays_Consecutive%20%2F%207)%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20totalPoints%20%5Blabel%3D%22Total%20Reward%20Calculation%22%2C%20shape%3Dparallelogram%2C%20fillcolor%3Dlightyellow%5D%3B%0A%20%20%20%20%0A%20%20%20%20start%20-%3E%20taskCompleted%3B%0A%20%20%20%20taskCompleted%20-%3E%20assignBP%20%5Blabel%3D%22Yes%22%5D%3B%0A%20%20%20%20taskCompleted%20-%3E%20totalPoints%20%5Blabel%3D%22No%22%2C%20style%3Ddashed%5D%3B%0A%20%20%20%20%0A%20%20%20%20assignBP%20-%3E%20checkLBE%3B%0A%20%20%20%20checkLBE%20-%3E%20assignLBE%20%5Blabel%3D%22POI%20%3C%20Avg%22%5D%3B%0A%20%20%20%20checkLBE%20-%3E%20checkTD%20%5Blabel%3D%22POI%20%3E%3D%20Avg%22%5D%3B%0A%20%20%20%20assignLBE%20-%3E%20checkTD%3B%0A%20%20%20%20%0A%20%20%20%20checkTD%20-%3E%20assignTD%20%5Blabel%3D%22Valid%20Time%20Slot%22%5D%3B%0A%20%20%20%20checkTD%20-%3E%20checkPP%20%5Blabel%3D%22Invalid%20Time%20Slot%22%5D%3B%0A%20%20%20%20assignTD%20-%3E%20checkPP%3B%0A%20%20%20%20%0A%20%20%20%20checkPP%20-%3E%20assignPP%20%5Blabel%3D%22Improved%20Response%20Time%22%5D%3B%0A%20%20%20%20checkPP%20-%3E%20checkStreak%20%5Blabel%3D%22No%20Improvement%22%5D%3B%0A%20%20%20%20assignPP%20-%3E%20checkStreak%3B%0A%20%20%20%20%0A%20%20%20%20checkStreak%20-%3E%20assignStreak%20%5Blabel%3D%22Maintained%20Streak%22%5D%3B%0A%20%20%20%20checkStreak%20-%3E%20totalPoints%20%5Blabel%3D%22No%20Streak%22%5D%3B%0A%20%20%20%20assignStreak%20-%3E%20totalPoints%3B%0A%7D
"""

import datetime
import hashlib
import random
from app.core.config import configs
from app.core.container import Container
from app.core.exceptions import InternalServerError
from app.engine.base_strategy import BaseStrategy
from app.schema.task_schema import SimulatedTaskPoints
from app.util.calculate_hash_simulated_strategy import (
    calculate_hash_simulated_strategy
)
from collections import defaultdict
from app.util.add_log import add_log
from graphviz import Digraph
import numpy as np


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
        dim: int(round(np.mean(vals))) if vals else 5
        for dim, vals in values.items()
    }

    return average_values


def get_dynamic_values_from_tasks(task, list_ids_tasks, all_records, user, variable_basic_points):
    """
    Calculates dynamic values based on user participation in tasks.

    Args:
        task (object): The task object.
        list_ids_tasks (list): A list of task IDs.
        all_records (list): A list of all task records.
        user (object): The user object.
        variable_basic_points (int): The base points per participation.

    Returns:
        dict: A dictionary containing calculated values for each dimension.
    """

    """
    task = Tasks(id=81ba53f3-7130-40ef-89bc-23dbb65b59d7, created_at=2025-02-25 13:57:00.197095+00:00, updated_at=2025-02-25 13:57:00.197095+00:00, externalTaskId=POI_a5bca879-3b11-4fc6-880b-b3d8b8aba839_Task_1111b063-5e3d-48c5-9532-259aaba7d03a, gameId=1f2f0e61-19f5-4e05-a8f7-f3f51fa46989, strategyId=greencrowdStrategy, status=open)
    _________________________________________________________
    list_ids_tasks = [{'id': UUID('f572f877-8eba-486a-b93c-948c9d85bcfb'), 'externalTaskId': 'POI_6623df1a-2486-40af-90f7-96b6bccde472_Task_20fcb063-5e3d-48c5-9532-259aaba7d03a'}, {'id': UUID('a7938e5c-80a7-4603-b325-da1a773b44c1'), 'externalTaskId': 'POI_d8fd6554-a140-42ff-8d73-fa314c0358bd_Task_30fcb063-5e3d-48c5-9532-259aaba7d03a'}, {'id': UUID('e321fbbb-6c78-4b10-a1e1-fe9e6d2b9e66'), 'externalTaskId': 'POI_3e134cfc-75a2-4e21-85e9-89983d98a819_Task_40fcb063-5e3d-48c5-9532-259aaba7d03a'}, {'id': UUID('3497366d-1fba-46d9-bc7b-9936a997daf4'), 'externalTaskId': 'POI_a908261b-2a21-41ef-a1f1-eb4e3eccde15_Task_50fcb063-5e3d-48c5-9532-259aaba7d03a'}, {'id': UUID('5e8c1e3a-0b8b-4ae1-a6a9-a479000a6b4b'), 'externalTaskId': 'POI_867a3095-e40c-4fdd-93f1-99f94596e9ab_Task_60fcb063-5e3d-48c5-9532-259aaba7d03a'}, {'id': UUID('9e66ea4f-da99-45c3-85da-d27501aa5c9c'), 'externalTaskId': 'POI_db490f8d-961e-4781-a201-44ad1e844bfa_Task_70fcb063-5e3d-48c5-9532-259aaba7d03a'}, {'id': UUID('d2ff40d6-02c0-448f-a970-49332bcc7217'), 'externalTaskId': 'POI_239b1cd2-4d6b-4e3e-980c-3f1c98b2838d_Task_80fcb063-5e3d-48c5-9532-259aaba7d03a'}, {'id': UUID('91ba53f3-7130-40ef-89bc-23dbb65b59d7'), 'externalTaskId': 'POI_a5bca879-3b11-4fc6-880b-b3d8b8aba839_Task_90fcb063-5e3d-48c5-9532-259aaba7d03a'}, {'id': UUID('81ba53f3-7130-40ef-89bc-23dbb65b59d7'), 'externalTaskId': 'POI_a5bca879-3b11-4fc6-880b-b3d8b8aba839_Task_1111b063-5e3d-48c5-9532-259aaba7d03a'}]
    _________________________________________________________
  all_records = [(UUID('21cd0e6d-fc4f-4e7a-8d1b-4f4c0eda643d'), datetime.datetime(2025, 2, 27, 11, 2, 57, 459658, tzinfo=datetime.timezone.utc), datetime.datetime(2025, 2, 27, 11, 2, 57, 459658, tzinfo=datetime.timezone.utc), 1, 'Valid Simulation', 'Points assigned by GAME', UUID('7f406292-88b8-404d-b6fa-46da221f008f'), UUID('f572f877-8eba-486a-b93c-948c9d85bcfb'), None), (UUID('ad526ada-04c8-4c38-a2d6-d858a756051a'), datetime.datetime(2025, 2, 27, 11, 3, 4, 845762, tzinfo=datetime.timezone.utc), datetime.datetime(2025, 2, 27, 11, 3, 4, 845762, tzinfo=datetime.timezone.utc), 1, 'Valid Simulation', 'Points assigned by GAME', UUID('7f406292-88b8-404d-b6fa-46da221f008f'), UUID('f572f877-8eba-486a-b93c-948c9d85bcfb'), None), (UUID('209a4813-066b-4d75-abce-8f925de3c946'), datetime.datetime(2025, 2, 27, 11, 23, 3, 377387, tzinfo=datetime.timezone.utc), datetime.datetime(2025, 2, 27, 11, 23, 3, 377387, tzinfo=datetime.timezone.utc), 1, 'Valid Simulation', 'Points assigned by GAME', UUID('7f406292-88b8-404d-b6fa-46da221f008f'), UUID('f572f877-8eba-486a-b93c-948c9d85bcfb'), None), (UUID('da71acc6-19ff-4187-ac82-febc68117611'), datetime.datetime(2025, 2, 27, 13, 12, 49, 264394, tzinfo=datetime.timezone.utc), datetime.datetime(2025, 2, 27, 13, 12, 49, 264394, tzinfo=datetime.timezone.utc), 1, 'Valid Simulation', 'Points assigned by GAME', UUID('7f406292-88b8-404d-b6fa-46da221f008f'), UUID('f572f877-8eba-486a-b93c-948c9d85bcfb'), None), (UUID('ddb8e98c-e84a-41ab-9762-5663d2000feb'), datetime.datetime(2025, 2, 27, 13, 19, 36, 777447, tzinfo=datetime.timezone.utc), datetime.datetime(2025, 2, 27, 13, 19, 36, 777447, tzinfo=datetime.timezone.utc), 1, 'Valid Simulation - Origin: Used simulation', 'Points assigned by GAME', UUID('7f406292-88b8-404d-b6fa-46da221f008f'), UUID('f572f877-8eba-486a-b93c-948c9d85bcfb'), None), (UUID('98410976-b318-4644-89b9-40e9f4203297'), datetime.datetime(2025, 2, 27, 13, 34, 58, 361496, tzinfo=datetime.timezone.utc), datetime.datetime(2025, 2, 27, 13, 34, 58, 361496, tzinfo=datetime.timezone.utc), 1, 'Valid Simulation - Origin: Used simulation', 'Points assigned by GAME', UUID('7f406292-88b8-404d-b6fa-46da221f008f'), UUID('f572f877-8eba-486a-b93c-948c9d85bcfb'), None), (UUID('07e154bb-66ed-48b0-99c5-10e977a7786b'), datetime.datetime(2025, 2, 27, 13, 44, 40, 350427, tzinfo=datetime.timezone.utc), datetime.datetime(2025, 2, 27, 13, 44, 40, 350427, tzinfo=datetime.timezone.utc), 1, 'Valid Simulation', 'Points assigned by GAME', UUID('7f406292-88b8-404d-b6fa-46da221f008f'), UUID('f572f877-8eba-486a-b93c-948c9d85bcfb'), None), (UUID('6489692b-af57-484b-b544-95071dfb89b0'), datetime.datetime(2025, 2, 27, 13, 44, 48, 893151, tzinfo=datetime.timezone.utc), datetime.datetime(2025, 2, 27, 13, 44, 48, 893151, tzinfo=datetime.timezone.utc), 1, 'Valid Simulation - Origin: Used simulation', 'Points assigned by GAME', UUID('7f406292-88b8-404d-b6fa-46da221f008f'), UUID('f572f877-8eba-486a-b93c-948c9d85bcfb'), None), (UUID('8511a173-35e3-440c-b3de-3676df563eaf'), datetime.datetime(2025, 2, 27, 13, 48, 45, 338685, tzinfo=datetime.timezone.utc), datetime.datetime(2025, 2, 27, 13, 48, 45, 338685, tzinfo=datetime.timezone.utc), 26, 'Valid Simulation - Origin: Used simulation', 'Points assigned by GAME', UUID('7f406292-88b8-404d-b6fa-46da221f008f'), UUID('f572f877-8eba-486a-b93c-948c9d85bcfb'), None), (UUID('59bdef62-72df-4b83-9ef6-a3f24e3ccb6a'), datetime.datetime(2025, 2, 27, 13, 50, 48, 976234, tzinfo=datetime.timezone.utc), datetime.datetime(2025, 2, 27, 13, 50, 48, 976234, tzinfo=datetime.timezone.utc), 1, 'Valid Simulation - Origin: Used simulation', 'Points assigned by GAME', UUID('7f406292-88b8-404d-b6fa-46da221f008f'), UUID('f572f877-8eba-486a-b93c-948c9d85bcfb'), None)]
    _________________________________________________________


    """
    task_id = str(task.id)
    task_externalTaskId_internal = str(task.externalTaskId)

    parts = task_externalTaskId_internal.split("_")
    poi_external_id = parts[1]
    task_external_id = parts[3]
    user_externalUserId = user.externalUserId

    # get count of tasks by poi_external_id using list_ids_tasks
    total_task_in_poi = []
    for task_in_list in list_ids_tasks:
        if task_external_id in task_in_list.get("externalTaskId"):
            total_task_in_poi.append(task_in_list)
    count_total_task_in_poi = len(total_task_in_poi)
    # calculate DIM_BP
    dim_bp_value = 0
    if (count_total_task_in_poi > 0):
        # 7 f572f877-8eba-486a-b93c-948c9d85bcfb
        count_unique_task_in_poi = 0
        # for total_task_in_poi
        for task_in_poi in total_task_in_poi:
            # task_in_poi = {'id': UUID('f572f877-8eba-486a-b93c-948c9d85bcfb'), 'externalTaskId': 'POI_6623df1a-2486-40af-90f7-96b6bccde472_Task_20fcb063-5e3d-48c5-9532-259aaba7d03a'}, {'id': UUID('a7938e5c-80a7-4603-b325-da1a773b44c1'), 'externalTaskId': 'POI_d8fd6554-a140-42ff-8d73-fa314c0358bd_Task_30fcb063-5e3d-48c5-9532-259aaba7d03a'}
            # check if task_in_poi is in all_records
            for record in all_records:
                if str(record.taskId) == str(task_in_poi.get("id")):
                    count_unique_task_in_poi += 1
                    break
            print('888888888888888888888888888888888888888888888888888888')

    print('0000000000000000000000.... ')
    print('0000000000000000000000.... ')
    print('0000000000000000000000.... ')
    print('0000000000000000000000.... ')
    print('0000000000000000000000.... ')
    print('0000000000000000000000.... ')
    print('0000000000000000000000.... ')
    print('0000000000000000000000.... ')
    print(count_unique_task_in_poi)
    print(count_total_task_in_poi)
    print(' ')
    print(' ')
    print(' ')
    print(' ')
    print(' ')
    dim_bp_value = int(
        round(variable_basic_points *
              (count_unique_task_in_poi / count_total_task_in_poi))
    )
    print(dim_bp_value)

    """
   user_task_participation=  defaultdict(<class 'set'>, {'6623df1a-2486-40af-90f7-96b6bccde472': {UUID('f572f877-8eba-486a-b93c-948c9d85bcfb')}, 'a5bca879-3b11-4fc6-880b-b3d8b8aba839': {UUID('91ba53f3-7130-40ef-89bc-23dbb65b59d7')}})
poi_tasks_map = defaultdict(<class 'list'>, {'6623df1a-2486-40af-90f7-96b6bccde472': [{'taskId': 'f572f877-8eba-486a-b93c-948c9d85bcfb', 'POITaskId': 'POI_6623df1a-2486-40af-90f7-96b6bccde472_Task_20fcb063-5e3d-48c5-9532-259aaba7d03a', 'externalTaskId': '20fcb063-5e3d-48c5-9532-259aaba7d03a'}], 'd8fd6554-a140-42ff-8d73-fa314c0358bd': [{'taskId': 'a7938e5c-80a7-4603-b325-da1a773b44c1', 'POITaskId': 'POI_d8fd6554-a140-42ff-8d73-fa314c0358bd_Task_30fcb063-5e3d-48c5-9532-259aaba7d03a', 'externalTaskId': '30fcb063-5e3d-48c5-9532-259aaba7d03a'}], '3e134cfc-75a2-4e21-85e9-89983d98a819': [{'taskId': 'e321fbbb-6c78-4b10-a1e1-fe9e6d2b9e66', 'POITaskId': 'POI_3e134cfc-75a2-4e21-85e9-89983d98a819_Task_40fcb063-5e3d-48c5-9532-259aaba7d03a', 'externalTaskId': '40fcb063-5e3d-48c5-9532-259aaba7d03a'}], 'a908261b-2a21-41ef-a1f1-eb4e3eccde15': [{'taskId': '3497366d-1fba-46d9-bc7b-9936a997daf4', 'POITaskId': 'POI_a908261b-2a21-41ef-a1f1-eb4e3eccde15_Task_50fcb063-5e3d-48c5-9532-259aaba7d03a', 'externalTaskId': '50fcb063-5e3d-48c5-9532-259aaba7d03a'}], '867a3095-e40c-4fdd-93f1-99f94596e9ab': [{'taskId': '5e8c1e3a-0b8b-4ae1-a6a9-a479000a6b4b', 'POITaskId': 'POI_867a3095-e40c-4fdd-93f1-99f94596e9ab_Task_60fcb063-5e3d-48c5-9532-259aaba7d03a', 'externalTaskId': '60fcb063-5e3d-48c5-9532-259aaba7d03a'}], 'db490f8d-961e-4781-a201-44ad1e844bfa': [{'taskId': '9e66ea4f-da99-45c3-85da-d27501aa5c9c', 'POITaskId': 'POI_db490f8d-961e-4781-a201-44ad1e844bfa_Task_70fcb063-5e3d-48c5-9532-259aaba7d03a', 'externalTaskId': '70fcb063-5e3d-48c5-9532-259aaba7d03a'}], '239b1cd2-4d6b-4e3e-980c-3f1c98b2838d': [{'taskId': 'd2ff40d6-02c0-448f-a970-49332bcc7217', 'POITaskId': 'POI_239b1cd2-4d6b-4e3e-980c-3f1c98b2838d_Task_80fcb063-5e3d-48c5-9532-259aaba7d03a', 'externalTaskId': '80fcb063-5e3d-48c5-9532-259aaba7d03a'}], 'a5bca879-3b11-4fc6-880b-b3d8b8aba839': [{'taskId': '91ba53f3-7130-40ef-89bc-23dbb65b59d7', 'POITaskId': 'POI_a5bca879-3b11-4fc6-880b-b3d8b8aba839_Task_90fcb063-5e3d-48c5-9532-259aaba7d03a', 'externalTaskId': '90fcb063-5e3d-48c5-9532-259aaba7d03a'}, {'taskId': '81ba53f3-7130-40ef-89bc-23dbb65b59d7', 'POITaskId': 'POI_a5bca879-3b11-4fc6-880b-b3d8b8aba839_Task_80fcb063-5e3d-48c5-9532-259aaba7d03a', 'externalTaskId': '80fcb063-5e3d-48c5-9532-259aaba7d03a'}]})
    """

    response = {
        "DIM_BP": dim_bp_value,
        "DIM_LBE": 0,
        "DIM_TD": 0,
        "DIM_PP": 0,
        "DIM_S": 0,
    }

    return response


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
        return hashlib.sha256((configs.SECRET_KEY + str(data_string)).encode("utf-8")).hexdigest()

    def simulate_strategy(
            self,

            data_to_simulate: dict = None,
            userGroup: str = "dynamic"
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

        task = data_to_simulate.get("task")
        allTasks = data_to_simulate.get("allTasks")
        external_user_id = data_to_simulate.get("externalUserId")

        if not task or not allTasks or not external_user_id:
            return InternalServerError("Missing data to simulate the strategy")

        total_simulated_points = 0

        DIM_BP = 0
        DIM_LBE = 0
        DIM_TD = 0
        DIM_PP = 0
        DIM_S = 0
        # RANDOM_RAGE ########################################################

        list_ids_tasks = []
        list_ids_tasks_to_ask = []
        for task in allTasks:
            list_ids_tasks_to_ask.append(task.id)
            list_ids_tasks.append({
                "id": task.id,
                "externalTaskId": task.externalTaskId
            })

        all_records = self.user_points_service.get_all_point_of_tasks_list(
            list_ids_tasks_to_ask, withData=True)

        if (userGroup == "random_range"):
            random_calculated = get_random_values_from_tasks(
                all_records)

            DIM_BP = random_calculated.get("DIM_BP")
            DIM_LBE = random_calculated.get("DIM_LBE")
            DIM_TD = random_calculated.get("DIM_TD")
            DIM_PP = random_calculated.get("DIM_PP")
            DIM_S = random_calculated.get("DIM_S")

        # END RANDOM_RAGE ########################################################

        # AVERAGE_SCORE ########################################################
        if (userGroup == "average_score"):
            average_calculated = get_average_values_from_tasks(
                task,
                all_records)

            DIM_BP = average_calculated.get("DIM_BP")
            DIM_LBE = average_calculated.get("DIM_LBE")
            DIM_TD = average_calculated.get("DIM_TD")
            DIM_PP = average_calculated.get("DIM_PP")
            DIM_S = average_calculated.get("DIM_S")

        # END AVERAGE_SCORE ########################################################

        # DYNAMIC_CALCULATION ########################################################
        if (userGroup == "dynamic_calculation"):
            user = self.user_service.get_user_by_externalUserId(
                external_user_id)
            dynamic_calculated = get_dynamic_values_from_tasks(
                task,
                list_ids_tasks,
                all_records,
                user,
                self.variable_basic_points)
            DIM_BP = dynamic_calculated.get("DIM_BP")
            DIM_LBE = dynamic_calculated.get("DIM_LBE")
            DIM_TD = dynamic_calculated.get("DIM_TD")
            DIM_PP = dynamic_calculated.get("DIM_PP")
            DIM_S = dynamic_calculated.get("DIM_S")
        # END DYNAMIC_CALCULATION ########################################################
        ###########################################################################################################################
        total_simulated_points = DIM_BP + DIM_LBE + DIM_TD + DIM_PP + DIM_S

        expiration_date = datetime.datetime.now() + datetime.timedelta(
            minutes=self.variable_simulation_valid_until)
        expiration_date = expiration_date.replace(tzinfo=datetime.timezone.utc)

        externalTaskId = task.externalTaskId
        return SimulatedTaskPoints(
            externalUserId=external_user_id,
            externalTaskId=str(task.externalTaskId),
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
            self, externalGameId, externalTaskId, externalUserId, data):
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
        case_name = '-'
        points = -1

        # destructuring data
        simulationHash = data.get("simulationHash")
        tasks = data.get("tasks")

        tasks_simulated = []
        for task in tasks:
            tasks_simulated.append(SimulatedTaskPoints(**task))
        tasks = tasks_simulated
        calculated_hash = calculate_hash_simulated_strategy(
            tasks, externalGameId, externalUserId)
        if calculated_hash != simulationHash:
            return points, "Invalid hash"

        isExpired = False
        # select externalTaskId from tasks where externalTaskId = taksId
        task = next(
            (task for task in tasks if str(task.externalTaskId)
             == str(externalTaskId)), None
        )

        callback_data = None
        previous_points = self.user_points_service.get_points_of_simulated_task(
            externalTaskId, simulationHash
        )
        if previous_points:

            game = self.game_service.get_game_by_external_id(externalGameId)

            tasks_simulated, externalGameId = await self.user_points_service.get_points_simulated_of_user_in_game(
                game.id, externalUserId, assign_control_group=True
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
                None
            )
            task = next(
                (task for task in tasks_simulated if task.externalTaskId ==
                 externalTaskId), None
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

                tasks_simulated, externalGameId = await self.user_points_service.get_points_simulated_of_user_in_game(
                    game.id, externalUserId, assign_control_group=True
                )
                callback_data = tasks_simulated
                simulationHash = calculate_hash_simulated_strategy(
                    tasks_simulated, externalGameId, externalUserId
                )
                task = next(
                    (task for task in tasks_simulated if task.externalTaskId ==
                     externalTaskId), None
                )
                if (case_name == "-"):
                    case_name = "Valid Simulation - Origin: Expired simulation"

            points = 0
            DIM_BP = task.dimensions[0].get("DIM_BP")
            DIM_LBE = task.dimensions[1].get("DIM_LBE")
            DIM_TD = task.dimensions[2].get("DIM_TD")
            DIM_PP = task.dimensions[3].get("DIM_PP")
            DIM_S = task.dimensions[4].get("DIM_S")

            print({
                "DIM_BP": DIM_BP,
                "DIM_LBE": DIM_LBE,
                "DIM_TD": DIM_TD,
                "DIM_PP": DIM_PP,
                "DIM_S": DIM_S
            })
            points = DIM_BP + DIM_LBE + DIM_TD + DIM_PP + DIM_S + 1
            if (case_name == "-"):
                case_name = "Valid Simulation"

        return points, case_name, callback_data
