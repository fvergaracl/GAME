from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

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
