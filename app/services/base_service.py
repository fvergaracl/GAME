from uuid import UUID


class BaseService:
    """
    Base service class providing common CRUD operations.

    Attributes:
        repository: The repository instance used for database operations.
    """

    def __init__(self, repository) -> None:
        """
        Initializes the BaseService with the provided repository.

        Args:
            repository: The repository instance.
        """
        self._repository = repository

    def get_list(self, schema):
        """
        Retrieves a list of items based on the provided schema.

        Args:
            schema: The schema for filtering the items.

        Returns:
            list: A list of items matching the schema.
        """
        return self._repository.read_by_options(schema)

    def get_by_id(self, id: UUID):
        """
        Retrieves an item by its ID.

        Args:
            id (UUID): The unique identifier of the item.

        Returns:
            object: The item with the given ID.
        """
        return self._repository.read_by_id(id)

    def add(self, schema):
        """
        Adds a new item using the provided schema.

        Args:
            schema: The schema representing the item to be added.

        Returns:
            object: The added item.
        """
        return self._repository.create(schema)

    def patch(self, id: UUID, schema):
        """
        Updates an item partially by its ID using the provided schema.

        Args:
            id (UUID): The unique identifier of the item.
            schema: The schema representing the updated data.

        Returns:
            object: The updated item.
        """
        return self._repository.update(id, schema)

    def patch_attr(self, id: UUID, attr: str, value):
        """
        Updates a specific attribute of an item by its ID.

        Args:
            id (UUID): The unique identifier of the item.
            attr (str): The attribute to be updated.
            value: The new value of the attribute.

        Returns:
            object: The updated item.
        """
        return self._repository.update_attr(id, attr, value)

    def put_update(self, id: UUID, schema):
        """
        Replaces an item entirely by its ID using the provided schema.

        Args:
            id (UUID): The unique identifier of the item.
            schema: The schema representing the new data.

        Returns:
            object: The updated item.
        """
        return self._repository.whole_update(id, schema)

    def remove_by_id(self, id: UUID):
        """
        Removes an item by its ID.

        Args:
            id (UUID): The unique identifier of the item.

        Returns:
            None
        """
        return self._repository.delete_by_id(id)
