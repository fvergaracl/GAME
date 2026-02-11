from contextlib import AbstractContextManager
from typing import Callable, Optional

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import configs
from app.core.exceptions import NotFoundError
from app.model.wallet import Wallet
from app.repository.base_repository import BaseRepository


class WalletRepository(BaseRepository):
    """
    Repository class for wallets.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for wallets.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=Wallet,
    ) -> None:
        """
        Initializes the WalletRepository with the provided session factory and
          model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for wallets.
        """
        super().__init__(session_factory, model)

    def upsert_points_balance(
        self,
        user_id,
        points_delta: int,
        api_key: Optional[str] = None,
        oauth_user_id: Optional[str] = None,
        session: Optional[Session] = None,
        auto_commit: bool = True,
    ) -> Wallet:
        """
        Atomically increments a user's wallet points balance.

        If no wallet exists for the user, it is created first. This method is
        safe under concurrent writes thanks to `ON CONFLICT ... DO UPDATE`.
        """
        if session is None and not auto_commit:
            raise ValueError(
                "auto_commit=False requires an external session managed by the caller."
            )
        if session is None:
            with self.session_factory() as managed_session:
                return self.upsert_points_balance(
                    user_id=user_id,
                    points_delta=points_delta,
                    api_key=api_key,
                    oauth_user_id=oauth_user_id,
                    session=managed_session,
                    auto_commit=auto_commit,
                )

        wallet_table = self.model.__table__
        insert_stmt = insert(wallet_table).values(
            userId=user_id,
            coinsBalance=0.0,
            pointsBalance=points_delta,
            conversionRate=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN,
            apiKey_used=api_key,
            oauth_user_id=oauth_user_id,
        )

        on_conflict_updates = {
            "pointsBalance": wallet_table.c.pointsBalance + points_delta,
            "updated_at": func.now(),
        }
        if api_key is not None:
            on_conflict_updates["apiKey_used"] = api_key
        if oauth_user_id is not None:
            on_conflict_updates["oauth_user_id"] = oauth_user_id

        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[wallet_table.c.userId],
            set_=on_conflict_updates,
        ).returning(wallet_table.c.id)

        wallet_id = session.execute(upsert_stmt).scalar_one()
        if auto_commit:
            session.commit()
        else:
            session.flush()

        wallet = session.query(self.model).filter(self.model.id == wallet_id).first()
        if wallet is None:
            raise NotFoundError(detail=f"Wallet not found by id: {wallet_id}")
        return wallet
