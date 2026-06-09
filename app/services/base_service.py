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
        """
        Return a filtered, paginated list of entities.

        Args:
            schema: Search schema with filters and ordering/pagination.

        Returns:
            dict[str, Any]: Items plus search metadata, as returned by the
            repository.
        """
        return await self._repository.read_by_options(schema)

    async def get_by_id(self, id: UUID) -> Any:
        """
        Fetch a single entity by primary key.

        Args:
            id (UUID): Primary key of the entity.

        Returns:
            Any: The matching entity.
        """
        return await self._repository.read_by_id(id)

    async def add(self, schema) -> Any:
        """
        Create a new entity from ``schema``.

        Args:
            schema: Pydantic schema describing the entity to create.

        Returns:
            Any: The persisted entity.
        """
        return await self._repository.create(schema)

    async def patch(self, id: UUID, schema) -> Any:
        """
        Partially update an entity, ignoring null fields.

        Args:
            id (UUID): Primary key of the entity to update.
            schema: Schema whose non-null fields are applied.

        Returns:
            Any: The updated entity.
        """
        return await self._repository.update(id, schema)

    async def patch_attr(self, id: UUID, attr: str, value) -> Any:
        """
        Update a single attribute of an entity.

        Args:
            id (UUID): Primary key of the entity.
            attr (str): Name of the attribute to set.
            value: New value for the attribute.

        Returns:
            Any: The updated entity.
        """
        return await self._repository.update_attr(id, attr, value)

    async def put_update(self, id: UUID, schema) -> Any:
        """
        Fully replace an entity's fields from ``schema``.

        Args:
            id (UUID): Primary key of the entity to replace.
            schema: Schema dumped in full into the update.

        Returns:
            Any: The updated entity.
        """
        return await self._repository.whole_update(id, schema)

    async def remove_by_id(self, id: UUID) -> None:
        """
        Delete an entity by primary key.

        Args:
            id (UUID): Primary key of the entity to delete.
        """
        return await self._repository.delete_by_id(id)
