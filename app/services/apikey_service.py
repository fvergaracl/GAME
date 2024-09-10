from app.repository.apikey_repository import (
    ApiKeyRepository
)
from app.services.base_service import BaseService


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

    async def create_api_key(self, apikeyPostBody):
        """
        Create an API key.

        Args:
            apikeyPostBody: The API key to create.

        Returns:
            The created API key.
        """
        print('************************')
        return await self.apikey_repository.create(apikeyPostBody)
