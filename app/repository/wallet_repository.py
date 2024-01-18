from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session
from app.model.wallet import Wallet
from app.repository.base_repository import BaseRepository


class WalletRepository(BaseRepository):

    def __init__(
        self,
        session_factory: Callable[
            ...,
            AbstractContextManager[Session]],
            model=Wallet) -> None:
        super().__init__(session_factory, model)
