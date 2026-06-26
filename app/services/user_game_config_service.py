from typing import Optional
from uuid import UUID

from app.repository.user_game_config_repository import UserGameConfigRepository
from app.schema.user_game_config_schema import (
    CreateUserGameConfig,
    UpdateUserGameConfig,
    UserGameConfigResponse,
)


class UserGameConfigService:
    """
    Service class for managing user-specific game configurations.
    """

    def __init__(self, repository: UserGameConfigRepository) -> None:
        self.repository = repository

    async def get_user_config(
        self, user_id: UUID, game_id: UUID
    ) -> Optional[UserGameConfigResponse]:
        """
        Fetch the per-user configuration for a game.

        Args:
            user_id (UUID): Internal user identifier.
            game_id (UUID): Internal game identifier.

        Returns:
            Optional[UserGameConfigResponse]: The config, or ``None`` if the
            user has none for that game.
        """
        config = await self.repository.get_by_user_and_game(user_id, game_id)
        return UserGameConfigResponse.model_validate(config) if config else None

    async def create_user_config(
        self, schema: CreateUserGameConfig
    ) -> UserGameConfigResponse:
        """
        Create (or upsert) a user's configuration for a game.

        Args:
            schema (CreateUserGameConfig): Config payload (user, game,
                experiment group and config data).

        Returns:
            UserGameConfigResponse: The persisted configuration.
        """
        config = await self.repository.create_or_update(
            schema.userId,
            schema.gameId,
            schema.experimentGroup,
            schema.configData,
        )
        return UserGameConfigResponse.model_validate(config)

    async def update_user_config(
        self, user_id: UUID, game_id: UUID, schema: UpdateUserGameConfig
    ) -> Optional[UserGameConfigResponse]:
        """
        Update an existing user's game configuration.

        Falls back to the current values for any field omitted in ``schema``.

        Args:
            user_id (UUID): Internal user identifier.
            game_id (UUID): Internal game identifier.
            schema (UpdateUserGameConfig): Fields to update.

        Returns:
            Optional[UserGameConfigResponse]: The updated config, or ``None``
            if no config exists for that user/game.
        """
        existing_config = await self.repository.get_by_user_and_game(user_id, game_id)
        if not existing_config:
            return None

        updated_config = await self.repository.create_or_update(
            user_id,
            game_id,
            schema.experimentGroup or existing_config.experimentGroup,
            schema.configData or existing_config.configData,
        )
        return UserGameConfigResponse.model_validate(updated_config)

    async def delete_user_config(self, user_id: UUID, game_id: UUID) -> bool:
        """
        Delete a user's configuration for a game.

        Args:
            user_id (UUID): Internal user identifier.
            game_id (UUID): Internal game identifier.

        Returns:
            bool: ``True`` if a configuration was deleted, ``False`` otherwise.
        """
        return await self.repository.delete(user_id, game_id)
