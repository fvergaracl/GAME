from app.repository.apikey_repository import (
    ApiKeyRepository
)
from app.services.base_service import BaseService
from app.util.generate_api_key import generate_api_key


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

    async def generate_api_key(self):
        """
        Generate a random API key.

        Returns:
            str: The generated API key.
        """
        exist_key = True
        while not (exist_key is None):
            api_key = generate_api_key()
            exist_key = self.apikey_repository.read_by_column(
                "apiKey", api_key, not_found_raise_exception=False)
        return api_key

    def create_api_key(self, apikeyPostBody):
        """
        Create an API key.

        Args:
            apikeyPostBody: The API key to create.

        Returns:
            The created API key.
        """
        return self.apikey_repository.create(apikeyPostBody)

    def get_all_api_keys(self):
        """
        Get all API keys.

        Returns:
            List[ApiKey]: All API keys in the database.
        """
        return self.apikey_repository.read_all()
