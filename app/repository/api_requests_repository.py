from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.model.api_requests import ApiRequests
from app.repository.base_repository import BaseRepository


class ApiRequestsRepository(BaseRepository):
    """
    Repository class for API Requests.

    Attributes:
        session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for API Requests.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=ApiRequests,
    ) -> None:
        """
        Initializes the ApiRequestsRepository with the provided session factory and
          model.

        Args:
            session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
              The session factory.
            model: The SQLAlchemy model class for API Requests.
        """
        super().__init__(session_factory, model)
