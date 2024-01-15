from domain.usecase.game_usecase import GameUseCase
from domain.entity.game import GameRead, Game
from domain.command.create_game_command import CreateGameCommand
from domain.repository.game_repository import GameRepositoryAdapter
from application.exception import (
    DuplicateGameException,
    GameNotFoundException,
)
from core.db import Transactional

class GameService(GameUseCase):
    def __init__(self):
        self.repository = GameRepositoryAdapter()

    async def get_game_list(
        self,
        *,
        limit: int = 12,
        prev: int | None = None,
    ) -> list[GameRead]:
        return await self.repository.get_games(limit=limit, prev=prev)

    @Transactional()
    async def create_game(self, *, command: CreateGameCommand) -> None:
        existing_game = await self.repository.get_game_by_external_id(
            external_game_id=command.external_game_id
        )
        if existing_game:
            raise DuplicateGameException

        game = Game.create(
            external_game_id=command.external_game_id,
            platform=command.platform,
            end_date_time=command.end_date_time,
            strategy_id=command.strategy_id
        )
        await self.repository.save(game=game)

    async def get_game_by_id(self, *, game_id: int) -> GameRead:
        game = await self.repository.get_game_by_id(game_id=game_id)
        if not game:
            raise GameNotFoundException

        return game

    async def get_game_by_external_id(self, *, external_game_id: str) -> GameRead:
        game = await self.repository.get_game_by_external_id(external_game_id=external_game_id)
        if not game:
            raise GameNotFoundException

        return game
