from app.repository.api_requests_repository import ApiRequestsRepository
from app.services.base_service import BaseService


class ApiRequestsService(BaseService):
    """
    Service class for API requests.

    Attributes:
        api_requests_repository (ApiRequestsRepository): Repository instance
          for API requests.
    """

    def __init__(self, api_requests_repository: ApiRequestsRepository):
        """
        Initializes the ApiRequestsService with the provided repository.

        Args:
            api_requests_repository (ApiRequestsRepository): The repository
              instance.
        """
        self.api_requests_repository = api_requests_repository
        super().__init__(api_requests_repository)
