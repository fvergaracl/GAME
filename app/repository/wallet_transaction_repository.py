from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session
from app.model.wallet_transactions import WalletTransactions
from app.repository.base_repository import BaseRepository


class WalletTransactionRepository(BaseRepository):
    """
    Repository class for wallet transactions.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for wallet transactions.
    """

    def __init__(
            self,
            session_factory: Callable[..., AbstractContextManager[Session]],
            model=WalletTransactions) -> None:
        """
        Initializes the WalletTransactionRepository with the provided session
          factory and model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for wallet transactions.
        """
        super().__init__(session_factory, model)
