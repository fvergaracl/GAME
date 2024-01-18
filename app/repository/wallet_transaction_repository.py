from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session
from app.model.wallet_transactions import WalletTransactions
from app.repository.base_repository import BaseRepository


class WalletTransactionRepository(BaseRepository):

    def __init__(
        self,
        session_factory: Callable[
            ...,
            AbstractContextManager[Session]],
            model=WalletTransactions) -> None:
        super().__init__(session_factory, model)
