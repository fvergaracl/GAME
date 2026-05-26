from typing import Optional
from uuid import UUID

from app.repository.user_game_config_repository import UserGameConfigRepository
from app.schema.user_game_config_schema import (CreateUserGameConfig,
                                                UpdateUserGameConfig,
                                                UserGameConfigResponse)


class UserGameConfigService:
    """
    Service class for managing user-specific game configurations.
    """

    def __init__(self, repository: UserGameConfigRepository):
        self.repository = repository

    async def get_user_config(
        self, user_id: UUID, game_id: UUID
    ) -> Optional[UserGameConfigResponse]:
        config = await self.repository.get_by_user_and_game(user_id, game_id)
        return UserGameConfigResponse.model_validate(config) if config else None

    async def create_user_config(
        self, schema: CreateUserGameConfig
    ) -> UserGameConfigResponse:
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
        existing_config = await self.repository.get_by_user_and_game(
            user_id, game_id
        )
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
        return await self.repository.delete(user_id, game_id)
