"""Points assignment (write path).

Resolves the strategy for a task, runs scoring (or takes the points directly)
and delegates the atomic write to
:meth:`PointsPersistenceMixin._persist_points_wallet_and_transaction`.
"""

import logging

from app.core.exceptions import (InternalServerError, NotFoundError,
                                 PreconditionFailedError)
from app.schema.task_schema import AssignedPointsToExternalUserId
from app.services.game_access import get_authorized_game
from app.services.strategy_service import resolve_realm_id
from app.services.user_points.persistence import PointsPersistenceMixin
from app.util.is_valid_slug import is_valid_slug

logger = logging.getLogger(__name__)


class PointsAssignmentMixin(PointsPersistenceMixin):
    async def assign_points_to_user_directly(
        self,
        gameId,
        externalTaskId,
        schema,
        api_key: str = None,
        *,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> AssignedPointsToExternalUserId:
        """
        Assign points to a user directly (non-simulated), using a predefined strategy.

        Args:
            gameId (UUID): ID of the game.
            externalTaskId (str): External task identifier.
            schema (PostAssignPointsToUser): Input data schema.
            api_key (str, optional): API key used to register the operation.

        Returns:
            AssignedPointsToExternalUserId: Information about the assigned points.
        """
        externalUserId = schema.externalUserId
        is_a_created_user = False

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
                not_found_message=f"Game with gameId {gameId} not found",
                only_one=True,
            )
        externalGameId = game.externalGameId

        task = await self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId
        )
        if not task:
            raise NotFoundError(f"Task not found with externalTaskId: {externalTaskId}")

        strategyId = task.strategyId
        # Same async resolver used by ``assign_points_to_user``. This
        # endpoint doesn't actually invoke ``calculate_points`` - it just
        # verifies the strategy exists for the realm - but using the
        # same resolver keeps custom and built-in ids consistent.
        realm_id = resolve_realm_id(api_key=api_key, oauth_user_id=oauth_user_id)
        strategy_instance = await self.strategy_service.get_strategy_instance(
            strategyId, realmId=realm_id
        )

        if not strategy_instance:
            raise NotFoundError(f"Strategy not found with id: {strategyId}")

        user = await self.users_repository.read_by_column(
            "externalUserId", externalUserId, not_found_raise_exception=False
        )
        if not user:
            if not is_valid_slug(externalUserId):
                raise PreconditionFailedError(
                    detail=f"Invalid externalUserId: {externalUserId}. Must be alphanumeric/underscore and 3–50 characters."
                )
            user = await self.users_repository.create_user_by_externalUserId(
                externalUserId
            )
            is_a_created_user = True

        data_to_add = schema.data or {}
        data_to_add["externalGameId"] = externalGameId
        data_to_add["externalTaskId"] = externalTaskId
        points = self._extract_points(data_to_add)
        if points is None:
            raise PreconditionFailedError(
                detail="Points cannot be None. Please provide a valid value."
            )
        idempotency_key = self._extract_idempotency_key(data_to_add)
        direct_case_name = "External_points_assigned"
        user_points, _, _ = await self._persist_points_wallet_and_transaction(
            user_id=user.id,
            task_id=task.id,
            points=points,
            case_name=direct_case_name,
            data_to_add=data_to_add,
            description="Points assigned directly to GAME",
            api_key=api_key,
            external_user_id=externalUserId,
            external_task_id=externalTaskId,
            idempotency_key=idempotency_key,
        )

        return AssignedPointsToExternalUserId(
            points=points,
            externalUserId=externalUserId,
            isACreatedUser=is_a_created_user,
            gameId=gameId,
            externalTaskId=externalTaskId,
            caseName=direct_case_name,
            created_at=str(user_points.created_at),
        )

    async def assign_points_to_user(
        self,
        gameId,
        externalTaskId,
        schema,
        isSimulated: bool = False,
        api_key: str = None,
        *,
        oauth_user_id: str = None,
        is_admin: bool = False,
        enforce_scope: bool = False,
    ) -> AssignedPointsToExternalUserId:
        """
        Assign points to a user.

        Args:
            gameId (UUID): The game ID.
            externalTaskId (str): The external task ID.
            schema (PostAssignPointsToUser): The schema with the data to
              assign points.
            api_key (str): The API key used.

        Returns:
            AssignedPointsToExternalUserId: The response with the points
              assigned.

        """
        externalUserId = schema.externalUserId
        is_a_created_user = False
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
        externalGameId = game.externalGameId
        task = await self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId
        )
        if not task:
            raise NotFoundError(f"Task not found with externalTaskId: {externalTaskId}")
        strategyId = task.strategyId
        # A single async resolver handles both built-in
        # registry ids and ``custom:<uuid>`` DSL strategies (scoped by
        # realmId so a tenant can't invoke another tenant's strategy).
        # The resolver raises NotFoundError itself when the strategy is
        # missing, so the previous separate ``get_strategy_by_id`` guard
        # is redundant and has been removed.
        realm_id = resolve_realm_id(api_key=api_key, oauth_user_id=oauth_user_id)
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
                externalUserId=externalUserId
            )
            is_a_created_user = True
        strategy_instance = await self.strategy_service.get_strategy_instance(
            strategyId, realmId=realm_id
        )
        data_to_add = schema.data
        try:
            if data_to_add is None:
                data_to_add = {}
            result_calculated_points = await strategy_instance.calculate_points(
                externalGameId=externalGameId,
                externalTaskId=externalTaskId,
                externalUserId=externalUserId,
                data=data_to_add,
            )
            points, case_name, callbackData = (result_calculated_points + (None,))[:3]
            logger.debug(
                "Calculated points result: points=%s case_name=%s callbackData_present=%s",
                points,
                case_name,
                callbackData is not None,
            )
            if callbackData is not None:
                data_to_add["callbackData"] = callbackData
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning(
                "Invalid scoring payload for externalTaskId=%s externalUserId=%s: %s",
                externalTaskId,
                externalUserId,
                str(exc),
                exc_info=True,
            )
            raise PreconditionFailedError(
                detail=(
                    "Invalid scoring payload for strategy execution. "
                    "Verify required fields and data types."
                )
            )
        except Exception:
            logger.exception(
                "Error calculating points for externalTaskId=%s externalUserId=%s",
                externalTaskId,
                externalUserId,
            )
            raise InternalServerError(
                detail=(
                    f"Error in calculate points for task with externalTaskId: {externalTaskId} and user with externalUserId: {externalUserId}. Please try again later or contact support"  # noqa
                )
            )
        if points == -1:
            raise PreconditionFailedError(detail=(case_name))
        if points is None:
            raise InternalServerError(
                detail=(
                    f"Points not calculated for task with externalTaskId: {externalTaskId} and user with externalUserId: {externalUserId}. Beacuse the strategy don't have condition to calculate it or the strategy don't have a case name"  # noqa
                )
            )
        if not case_name:
            case_name = getattr(schema, "caseName", None)
        if not case_name:
            raise InternalServerError(
                detail=(
                    f"Case name not resolved for task with externalTaskId: {externalTaskId} and user with externalUserId: {externalUserId}"  # noqa
                )
            )
        idempotency_key = self._extract_idempotency_key(data_to_add)
        user_points, _, _ = await self._persist_points_wallet_and_transaction(
            user_id=user.id,
            task_id=task.id,
            points=points,
            case_name=case_name,
            data_to_add=data_to_add,
            description="Points assigned by GAME",
            api_key=api_key,
            external_user_id=externalUserId,
            external_task_id=externalTaskId,
            idempotency_key=idempotency_key,
        )

        response = AssignedPointsToExternalUserId(
            points=points,
            externalUserId=externalUserId,
            isACreatedUser=is_a_created_user,
            gameId=gameId,
            externalTaskId=externalTaskId,
            caseName=case_name,
            created_at=str(user_points.created_at),
        )
        return response
