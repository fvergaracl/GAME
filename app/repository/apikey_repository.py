from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.api_key import ApiKey
from app.repository.base_repository import BaseRepository


class ApiKeyRepository(BaseRepository):
    """
    Repository class for API keys.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=ApiKey,
    ) -> None:
        super().__init__(session_factory, model)

    async def read_all(self, page: int = 1, page_size: int = 100):
        """
        Reads all API keys ordered by created_at desc.
        """
        max_page_size = 100
        if page_size > max_page_size:
            page_size = max_page_size

        async with self.session_factory() as session:
            stmt = (
                select(self.model)
                .order_by(self.model.created_at.desc())
                .limit(page_size)
                .offset((page - 1) * page_size)
            )
            return (await session.execute(stmt)).scalars().all()
