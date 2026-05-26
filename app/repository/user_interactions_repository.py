from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.model.user_interactions import UserInteractions
from app.repository.base_repository import BaseRepository


class UserInteractionsRepository(BaseRepository):
    """
    Repository class for User interactions.

    Attributes:
        session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for User interactions.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=UserInteractions,
    ) -> None:
        """
        Initializes the UserInteractionsRepository with the provided session
          factory and model.

        Args:
            session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
              The session factory.
            model: The SQLAlchemy model class for User interactions.
        """
        super().__init__(session_factory, model)
