from typing import Optional
from uuid import UUID

from app.repository.user_game_config_repository import UserGameConfigRepository
from app.schema.user_game_config_schema import (CreateUserGameConfig,
                                                UpdateUserGameConfig,
                                                UserGameConfigResponse)


class UserGameConfigService:
    """
    Service class for managing user-specific game configurations.

    Attributes:
        repository (UserGameConfigRepository): Repository instance for managing
          user game configurations.
    """

    def __init__(self, repository: UserGameConfigRepository):
        """
        Initializes the UserGameConfigService with the provided repository.

        Args:
            repository (UserGameConfigRepository): The repository instance for
              user game configurations.
        """
        self.repository = repository

    def get_user_config(
        self, user_id: UUID, game_id: UUID
    ) -> Optional[UserGameConfigResponse]:
        """
        Retrieves the user-specific configuration for a given game.

        Args:
            user_id (UUID): The user ID.
            game_id (UUID): The game ID.

        Returns:
            Optional[UserGameConfigResponse]: The user-game configuration if
              found, otherwise None.
        """
        config = self.repository.get_by_user_and_game(user_id, game_id)
        return UserGameConfigResponse.from_orm(config) if config else None

    def create_user_config(
        self, schema: CreateUserGameConfig
    ) -> UserGameConfigResponse:
        """
        Creates a new user game configuration.

        Args:
            schema (CreateUserGameConfig): The schema containing configuration
              details.

        Returns:
            UserGameConfigResponse: The created user-game configuration.
        """
        config = self.repository.create_or_update(
            schema.userId, schema.gameId, schema.experimentGroup, schema.configData
        )
        return UserGameConfigResponse.from_orm(config)

    def update_user_config(
        self, user_id: UUID, game_id: UUID, schema: UpdateUserGameConfig
    ) -> Optional[UserGameConfigResponse]:
        """
        Updates an existing user-game configuration.

        Args:
            user_id (UUID): The user ID.
            game_id (UUID): The game ID.
            schema (UpdateUserGameConfig): The schema containing updated
              configuration details.

        Returns:
            Optional[UserGameConfigResponse]: The updated configuration if it
              exists, otherwise None.
        """
        existing_config = self.repository.get_by_user_and_game(user_id, game_id)
        if not existing_config:
            return None

        updated_config = self.repository.create_or_update(
            user_id,
            game_id,
            schema.experimentGroup or existing_config.experimentGroup,
            schema.configData or existing_config.configData,
        )
        return UserGameConfigResponse.from_orm(updated_config)

    def delete_user_config(self, user_id: UUID, game_id: UUID) -> bool:
        """
        Deletes a user-game configuration.

        Args:
            user_id (UUID): The user ID.
            game_id (UUID): The game ID.

        Returns:
            bool: True if deleted successfully, False otherwise.
        """
        return self.repository.delete(user_id, game_id)
