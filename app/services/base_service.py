from typing import Any
from uuid import UUID


class BaseService:
    """
    Async base service class providing common CRUD operations on top of
    an async repository.
    """

    def __init__(self, repository) -> None:
        self._repository = repository

    async def get_list(self, schema) -> dict[str, Any]:
        return await self._repository.read_by_options(schema)

    async def get_by_id(self, id: UUID) -> Any:
        return await self._repository.read_by_id(id)

    async def add(self, schema) -> Any:
        return await self._repository.create(schema)

    async def patch(self, id: UUID, schema) -> Any:
        return await self._repository.update(id, schema)

    async def patch_attr(self, id: UUID, attr: str, value) -> Any:
        return await self._repository.update_attr(id, attr, value)

    async def put_update(self, id: UUID, schema) -> Any:
        return await self._repository.whole_update(id, schema)

    async def remove_by_id(self, id: UUID) -> None:
        return await self._repository.delete_by_id(id)
