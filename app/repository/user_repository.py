from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.users import Users
from app.repository.base_repository import BaseRepository


class UserRepository(BaseRepository):

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=Users,
    ) -> None:
        super().__init__(session_factory, model)

    def create_user_by_externalUserId(self, externalUserId: str):
        with self.session_factory() as session:
            user = Users(externalUserId=externalUserId)
            session.add(user)
            session.commit()
            return user
