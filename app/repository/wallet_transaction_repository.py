from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.model.wallet_transactions import WalletTransactions
from app.repository.base_repository import BaseRepository


class WalletTransactionRepository(BaseRepository):
    """
    Repository class for wallet transactions.

    Attributes:
        session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for wallet transactions.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=WalletTransactions,
    ) -> None:
        """
        Initializes the WalletTransactionRepository with the provided session
          factory and model.

        Args:
            session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
              The session factory.
            model: The SQLAlchemy model class for wallet transactions.
        """
        super().__init__(session_factory, model)
