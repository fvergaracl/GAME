from contextlib import AbstractContextManager
from typing import Callable, Optional

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
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

    def get_or_create_by_externalUserId(
        self,
        externalUserId: str,
        oauth_user_id: Optional[str] = None,
        session: Optional[Session] = None,
        auto_commit: bool = True,
    ) -> Users:
        """
        Returns an existing user by externalUserId or creates it atomically.

        Uses PostgreSQL ON CONFLICT to avoid read-then-create races and reduce
        roundtrips on hot write endpoints.
        """
        if session is None and not auto_commit:
            raise ValueError(
                "auto_commit=False requires an external session managed by the caller."
            )
        if session is None:
            with self.session_factory() as managed_session:
                return self.get_or_create_by_externalUserId(
                    externalUserId=externalUserId,
                    oauth_user_id=oauth_user_id,
                    session=managed_session,
                    auto_commit=auto_commit,
                )

        users_table = self.model.__table__
        insert_values = {
            "externalUserId": externalUserId,
            "oauth_user_id": oauth_user_id,
        }
        insert_stmt = insert(users_table).values(**insert_values)

        update_values = {"updated_at": func.now()}
        if oauth_user_id is not None:
            update_values["oauth_user_id"] = oauth_user_id

        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[users_table.c.externalUserId],
            set_=update_values,
        ).returning(users_table.c.id)

        user_id = session.execute(upsert_stmt).scalar_one()
        if auto_commit:
            session.commit()
        else:
            session.flush()

        user = session.query(self.model).filter(self.model.id == user_id).first()
        if user is None:
            raise NotFoundError(
                detail=f"User not found after upsert by externalUserId: {externalUserId}"
            )
        return user
