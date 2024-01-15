from abc import ABC, abstractmethod
from domain.entity.game import Game

class GameRepo(ABC):
    @abstractmethod
    async def get_games(
        self,
        *,
        limit: int = 12,
        prev: int | None = None,
    ) -> list[Game]:
        """Get game list"""

    @abstractmethod
    async def get_game_by_external_id(
        self,
        *,
        external_game_id: str
    ) -> Game | None:
        """Get game by external game ID"""

    @abstractmethod
    async def get_game_by_id(self, *, game_id: int) -> Game | None:
        """Get game by id"""

    @abstractmethod
    async def save(self, *, game: Game) -> None:
        """Save game"""
