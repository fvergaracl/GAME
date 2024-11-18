from app.repository.oauth_users_repository import OAuthUsersRepository
from app.services.base_service import BaseService


class OAuthUsersService(BaseService):
    """
    Service class for managing OAuth users records.

    Attributes:
        oauth_users_repository (OAuthUsersRepository): Repository instance for
            OAuth users.

    """

    def __init__(self, oauth_users_repository: OAuthUsersRepository):
        """
        Initializes the OAuthUsersService with the provided repositories and
          services.

        Args:
            oauth_users_repository: The Oauth users repository instance.
        """
        self.oauth_users_repository = oauth_users_repository
        super().__init__(oauth_users_repository)
