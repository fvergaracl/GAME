"""
Aggregator for /games endpoints.

The original monolithic implementation was split by sub-resource into
``games_crud``, ``games_strategy``, ``games_tasks``, ``games_points`` and
``games_users``. This module only:

* Combines those sub-routers into a single ``router`` exposed to the API.
* Re-exports endpoint callables and shared module-level symbols so existing
  callers and tests (which import them as ``app.api.v1.endpoints.games.X``)
  keep working without churn.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (games_crud, games_points, games_strategy,
                                  games_tasks, games_users)
from app.api.v1.endpoints.games_common import (_extract_api_key_from_header,
                                               _extract_db_error_code,
                                               _extract_oauth_user_id_from_token,
                                               _game_access_kwargs,
                                               _map_write_exception,
                                               _resolve_correlation_id,
                                               _resolve_idempotency_key)
from app.core.config import configs
from app.middlewares.valid_access_token import valid_access_token
from app.util.add_log import add_log
from app.util.calculate_hash_simulated_strategy import calculate_hash_simulated_strategy
from app.util.check_role import check_role

# CRUD endpoints
from app.api.v1.endpoints.games_crud import (create_game, delete_game_by_id,
                                             get_game_by_id, get_games_list,
                                             patch_game)
# Strategy
from app.api.v1.endpoints.games_strategy import get_strategy_by_gameId
# Task management on a game
from app.api.v1.endpoints.games_tasks import (create_task, create_tasks_bulk,
                                              get_task_by_gameId_taskId,
                                              get_task_list)
# Points / actions
from app.api.v1.endpoints.games_points import (assign_points_to_user,
                                               get_points_by_gameId,
                                               get_points_by_gameId_with_details,
                                               get_points_by_task_id,
                                               get_points_by_task_id_with_details,
                                               get_points_of_user_by_task_id,
                                               get_points_of_user_in_game,
                                               get_points_simulated_of_user_in_game,
                                               user_action_in_task)
# Users in game
from app.api.v1.endpoints.games_users import get_users_by_gameId

router = APIRouter()
router.include_router(games_crud.router)
router.include_router(games_strategy.router)
router.include_router(games_tasks.router)
router.include_router(games_points.router)
router.include_router(games_users.router)

__all__ = [
    "router",
    # shared module-level helpers (re-exported for tests)
    "_extract_api_key_from_header",
    "_extract_db_error_code",
    "_extract_oauth_user_id_from_token",
    "_game_access_kwargs",
    "_map_write_exception",
    "_resolve_correlation_id",
    "_resolve_idempotency_key",
    # external symbols re-exported for tests
    "add_log",
    "calculate_hash_simulated_strategy",
    "check_role",
    "configs",
    "valid_access_token",
    # endpoint callables
    "assign_points_to_user",
    "create_game",
    "create_task",
    "create_tasks_bulk",
    "delete_game_by_id",
    "get_game_by_id",
    "get_games_list",
    "get_points_by_gameId",
    "get_points_by_gameId_with_details",
    "get_points_by_task_id",
    "get_points_by_task_id_with_details",
    "get_points_of_user_by_task_id",
    "get_points_of_user_in_game",
    "get_points_simulated_of_user_in_game",
    "get_strategy_by_gameId",
    "get_task_by_gameId_taskId",
    "get_task_list",
    "get_users_by_gameId",
    "patch_game",
    "user_action_in_task",
]
