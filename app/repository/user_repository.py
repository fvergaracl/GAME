from contextlib import AbstractContextManager
from typing import Callable, Optional

from sqlalchemy.exc import IntegrityError
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

    async def create_user_by_externalUserId(
        self,
        externalUserId: str,
        oauth_user_id: Optional[str] = None,
    ) -> Users:
        """
        Creates a new user with the provided external user ID.

        Args:
            externalUserId (str): The external user ID.
            oauth_user_id (Optional[str]): The OAuth user ID.

        Returns:
            Users: The created user or the already-existing user when a
              concurrent insert race happens.
        """
        with self.session_factory() as session:
            user = Users(externalUserId=externalUserId, oauth_user_id=oauth_user_id)
            session.add(user)
            try:
                session.commit()
                session.refresh(user)
                return user
            except IntegrityError:
                # Concurrency-safe behavior for unique externalUserId:
                # if another transaction created the same user first,
                # return that row instead of bubbling a 500.
                session.rollback()
                existing_user = (
                    session.query(self.model)
                    .filter_by(externalUserId=externalUserId)
                    .first()
                )
                if existing_user is not None:
                    return existing_user
                raise
