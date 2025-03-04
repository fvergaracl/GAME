from app.repository.user_interactions_repository import UserInteractionsRepository
from app.services.base_service import BaseService


class UserInteractionsService(BaseService):
    """
    Service class for User Interactions.

    Attributes:
        user_interactions_repository (UserInteractionsRepository): Repository
          instance for User Interactions.
    """

    def __init__(self, user_interactions_repository: UserInteractionsRepository):
        """
        Initializes the UserInteractionsService with the provided repository.

        Args:
            user_interactions_repository (UserInteractionsRepository): The
              repository instance.
        """
        self.user_interactions_repository = user_interactions_repository
        super().__init__(user_interactions_repository)
