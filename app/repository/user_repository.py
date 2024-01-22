from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session
from app.model.users import Users
from app.repository.base_repository import BaseRepository
from app.schema.user_schema import BaseUser
from app.schema.wallet_schema import BaseWalletOnlyUserId


class UserRepository(BaseRepository):

    def __init__(
        self,
        session_factory: Callable[
            ...,
            AbstractContextManager[Session]],
            model=Users) -> None:
        super().__init__(session_factory, model)
