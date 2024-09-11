from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.api_key import ApiKey
from app.repository.base_repository import BaseRepository


class ApiKeyRepository(BaseRepository):
    """
    Repository class for API keys.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for API keys.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=ApiKey,
    ) -> None:
        """
        Initializes the ApiKeyRepository with the provided session factory and
          model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for API keys.
        """
        super().__init__(session_factory, model)

    def read_all(self, page: int = 1, page_size: int = 100):
        """
        Reads all API keys. Order by created_at.

        Args:
            page (int): The page number.
            page_size (int): The number of items per page.

        Returns:
            List[ApiKey]: All API keys in the database.

        """
        max_page_size = 100
        if page_size > max_page_size:
            page_size = max_page_size

        with self.session_factory() as session:
            return (
                session.query(self.model)
                .order_by(self.model.created_at.desc())
                .limit(page_size)
                .offset((page - 1) * page_size)
                .all()
            )
