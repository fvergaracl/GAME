from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.users import Users
from app.repository.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """
    Repository class for users.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for users.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=Users,
    ) -> None:
        """
        Initializes the UserRepository with the provided session factory and
          model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for users.
        """
        super().__init__(session_factory, model)

    def create_user_by_externalUserId(
        self, externalUserId: str, oauth_user_id: str
    ) -> Users:
        """
        Creates a new user with the provided external user ID.

        Args:
            externalUserId (str): The external user ID.
            oauth_user_id (str): The OAuth user ID.

        Returns:
            Users: The created user.
        """
        with self.session_factory() as session:
            user = Users(externalUserId=externalUserId, oauth_user_id=oauth_user_id)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
