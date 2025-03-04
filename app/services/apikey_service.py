from fastapi import Security
from fastapi.security.api_key import APIKeyHeader

from app.core.exceptions import ForbiddenError
from app.repository.apikey_repository import ApiKeyRepository
from app.services.base_service import BaseService
from app.util.generate_api_key import generate_api_key
from app.util.response import Response

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


class ApiKeyService(BaseService):
    """
    Service class for API keys.

    Attributes:
        apikey_repository (ApiKeyRepository): Repository instance for API keys.
    """

    def __init__(self, apikey_repository: ApiKeyRepository):
        """
        Initializes the ApiKeyService with the provided repository.

        Args:
            apikey_repository (ApiKeyRepository): The repository instance.
        """
        self.apikey_repository = apikey_repository
        super().__init__(apikey_repository)

    async def generate_api_key_service(self):
        """
        Generate a random API key.

        Returns:
            str: The generated API key.
        """
        exist_key = True
        while not (exist_key is None):
            api_key = generate_api_key()
            exist_key = self.apikey_repository.read_by_column(
                "apiKey", api_key, not_found_raise_exception=False
            )
        return api_key

    async def create_api_key(self, apikeyPostBody):
        """
        Create an API key.

        Args:
            apikeyPostBody: The API key to create.

        Returns:
            The created API key.
        """
        return await self.apikey_repository.create(apikeyPostBody)

    def get_all_api_keys(self):
        """
        Get all API keys.

        Returns:
            List[ApiKey]: All API
        """
        return self.apikey_repository.read_all()

    @staticmethod
    def get_api_key_header(
        api_key: str = Security(api_key_header),
    ):
        from app.core.container import Container

        """
        Get an API key by header.

        Args:
            api_key: The API key to get.

        Returns:
            ApiKey: The API key with the provided header.
        """
        if api_key is None:
            return Response.fail(error=ForbiddenError("API key not provided."))
        api_key_Repository = Container.apikey_repository()
        api_key_in_db = api_key_Repository.read_by_column(
            "apiKey", api_key, not_found_raise_exception=False
        )
        if api_key_in_db is None:
            raise ForbiddenError("API key is invalid or does not exist.")
        if not api_key_in_db.active:
            raise ForbiddenError("API key is inactive. Please contact an admin.")
        return Response.ok(data=api_key_in_db)
