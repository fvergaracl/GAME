"""Atomic persistence of a points assignment.

Writes the ``user_points`` row, the wallet balance increment and the wallet
transaction inside a single DB transaction, with idempotency-key support.
"""

from typing import Any

from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError

from app.core.exceptions import InternalServerError
from app.schema.user_points_schema import UserPointsAssign
from app.schema.wallet_transaction_schema import BaseWalletTransaction
from app.services.user_points._base import UserPointsContext


class PointsPersistenceMixin(UserPointsContext):
    @staticmethod
    def _extract_points(data) -> int | None:
        """
        Read a ``points`` value from a dict or object payload.

        Args:
            data: Either a mapping or an object exposing ``points``.

        Returns:
            int | None: The points value, or ``None`` if absent.
        """
        if isinstance(data, dict):
            return data.get("points")
        return getattr(data, "points", None)

    @staticmethod
    def _extract_idempotency_key(data) -> str | None:
        """
        Derive an idempotency key from common identifier fields.

        Checks ``eventId``, ``idempotencyKey`` and ``correlationId`` in order
        and returns the first non-empty string value.

        Args:
            data: The event payload (only dicts are inspected).

        Returns:
            str | None: The stripped idempotency key, or ``None`` if none
            present.
        """
        if not isinstance(data, dict):
            return None
        for key in ("eventId", "idempotencyKey", "correlationId"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    async def _persist_points_wallet_and_transaction(
        self,
        *,
        user_id,
        task_id,
        points: int,
        case_name: str,
        data_to_add: dict,
        description: str,
        api_key: str,
        external_user_id: str,
        external_task_id: str,
        idempotency_key: str = None,
    ) -> tuple[Any, Any, Any]:
        """
        Persists points assignment, wallet increment and wallet transaction in
        one database transaction.
        """
        async with self.user_points_repository.session_factory() as session:
            try:
                if idempotency_key:
                    existing_points = await self.user_points_repository.read_by_user_task_and_idempotency(
                        user_id=user_id,
                        task_id=task_id,
                        idempotency_key=idempotency_key,
                        session=session,
                    )
                    if existing_points is not None:
                        return existing_points, None, None

                user_points_schema = UserPointsAssign(
                    userId=str(user_id),
                    taskId=str(task_id),
                    points=points,
                    caseName=case_name,
                    data=data_to_add,
                    description=description,
                    apiKey_used=api_key,
                    idempotencyKey=idempotency_key,
                )
                user_points = await self.user_points_repository.create(
                    user_points_schema,
                    session=session,
                    auto_commit=False,
                )

                wallet = await self.wallet_repository.upsert_points_balance(
                    user_id=user_id,
                    points_delta=points,
                    api_key=api_key,
                    session=session,
                    auto_commit=False,
                )

                wallet_transaction = BaseWalletTransaction(
                    transactionType="AssignPoints",
                    points=points,
                    coins=0,
                    data=data_to_add,
                    appliedConversionRate=0,
                    walletId=str(wallet.id),
                    apiKey_used=api_key,
                )
                transaction = await self.wallet_transaction_repository.create(
                    wallet_transaction,
                    session=session,
                    auto_commit=False,
                )
                if not transaction:
                    raise InternalServerError(
                        detail=(
                            f"Wallet transaction not created for user {external_user_id} "
                            f"and task {external_task_id}"
                        )
                    )

                await session.commit()
                return user_points, wallet, transaction
            except (IntegrityError, DataError, ProgrammingError):
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                raise
