"""Points simulation (non-persisting).

Runs built-in strategies' ``simulate_strategy`` for a user across a game's
tasks without writing anything. Custom DSL strategies are skipped here; they
have their own dedicated simulate endpoint.
"""

import logging
from collections import Counter
from typing import Any

from app.core.exceptions import NotFoundError, PreconditionFailedError
from app.schema.user_game_config_schema import CreateUserGameConfig
from app.services.game_access import get_authorized_game
from app.services.strategy_service import is_custom_strategy_id
from app.services.user_points._base import UserPointsContext
from app.util.is_valid_slug import is_valid_slug

logger = logging.getLogger(__name__)


class PointsSimulationMixin(UserPointsContext):
    async def get_points_simulated_of_user_in_game(
        self,
        gameId,
        externalUserId,
        oauth_user_id: str = None,
        assign_control_group: bool = False,
        *,
        api_key: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> tuple[list[Any], str]:
        """
        Simulates the assignment of points for a user without persisting the
          changes.

        Args:
            gameId (UUID): The ID of the game.
            externalTaskId (str): The external task ID.
            schema: The schema containing user and action data.
            oauth_user_id (str): The OAuth user ID.

        Returns:
            dict: Simulation result with calculated points and case name.
        """
        if enforce_scope:
            game = await get_authorized_game(
                self.game_repository,
                gameId,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
                is_admin=is_admin,
            )
        else:
            game = await self.game_repository.read_by_column(
                column="id",
                value=gameId,
                not_found_message=(f"Game with gameId {gameId} not found"),
                only_one=True,
            )
        all_tasks = await self.task_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        if not all_tasks:
            raise NotFoundError(detail=f"Tasks not found by gameId: {game.id}")

        # First: Check if all strategies exist. Custom DSL strategies
        # (``custom:<uuid>``) live in the DB and have their own
        # ``/v1/strategies/custom/{id}/simulate`` endpoint; the legacy
        # simulator only operates on built-ins, so we just skip the
        # existence check for custom ids here. They will be filtered out
        # again in the per-strategy loop below.
        strategy = None
        for task in all_tasks:
            strategyId = task.strategyId
            if is_custom_strategy_id(strategyId):
                continue
            strategy = self.strategy_service.get_strategy_by_id(strategyId)

            if not strategy:
                raise NotFoundError(
                    f"One of the strategies not found with id: {strategyId} for task with externalTaskId: {task.externalTaskId}"  # noqa
                )

        user = await self.users_repository.read_by_column(
            "externalUserId", externalUserId, not_found_raise_exception=False
        )
        if not user:
            is_valid_externalUserId = is_valid_slug(externalUserId)
            if not is_valid_externalUserId:
                raise PreconditionFailedError(
                    detail=(
                        f"Invalid externalUserId: {externalUserId}. externalUserId should be a valid (Should have only alphanumeric characters and Underscore . Length should be between 3 and 50)"  # noqa
                    )
                )
            user = await self.users_repository.create_user_by_externalUserId(
                externalUserId=externalUserId,
                oauth_user_id=oauth_user_id,
            )
        userGroup = None
        if assign_control_group:
            user_config = await self.users_game_config_repository.read_by_columns(
                {"userId": user.id, "gameId": game.id},
                only_one=True,
                not_found_raise_exception=False,
            )
            if user_config:
                userGroup = user_config.experimentGroup
            if not userGroup:
                group_control = ["random_range", "average_score", "dynamic_calculation"]
                all_users = await self.users_game_config_repository.get_all_users_by_gameId(
                    game.id
                )
                group_counts = Counter(
                    user_config.experimentGroup for user_config in all_users
                )
                min_group = min(group_control, key=lambda g: group_counts.get(g, 0))
                userGroup = min_group
                new_user_config = CreateUserGameConfig(
                    userId=str(user.id),
                    gameId=str(game.id),
                    experimentGroup=userGroup,
                    configData={},
                )

                user_config = await self.users_game_config_repository.create(
                    new_user_config
                )

        grouped_by_strategyId = {}
        for task in all_tasks:
            strategy_id_applied = task.strategyId
            if strategy_id_applied not in grouped_by_strategyId:
                grouped_by_strategyId[strategy_id_applied] = []
            grouped_by_strategyId[strategy_id_applied].append(task)

        response = []

        user_last_task = await self.user_points_repository.get_last_task_by_userId(user.id)
        externalUserId = user.externalUserId

        for strategy_id_applied, tasks in grouped_by_strategyId.items():
            # Custom DSL strategies don't implement ``simulate_strategy``
            # — they use the dedicated DSL simulate endpoint. Skip them
            # here so a game that mixes built-in and custom strategies
            # still returns sensible simulator output for the built-ins.
            if is_custom_strategy_id(strategy_id_applied):
                continue
            strategy_instance = self.strategy_service.get_Class_by_id(
                strategy_id_applied
            )
            # check if strategy_instance have simulate_strategy
            if not hasattr(strategy_instance, "simulate_strategy"):
                raise NotFoundError(
                    f"Strategy with id: {strategy_id_applied} don't have simulate_strategy method"
                )
            for task in tasks:
                data_to_simulate = {
                    "task": task,
                    "allTasks": tasks,
                    "externalUserId": externalUserId,
                }
                try:
                    task_simulation = strategy_instance.simulate_strategy(
                        data_to_simulate=data_to_simulate,
                        userGroup=userGroup,
                        user_last_task=user_last_task,
                    )
                    response.append(task_simulation)
                except Exception:
                    logger.exception(
                        "Error simulating strategy=%s for gameId=%s externalUserId=%s taskId=%s",  # noqa
                        strategy_id_applied,
                        gameId,
                        externalUserId,
                        task.externalTaskId,
                    )

        externalGameId = game.externalGameId
        return response, externalGameId
