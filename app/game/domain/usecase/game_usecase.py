from abc import ABC, abstractmethod
from domain.entity.game import Game
from domain.command.create_game_command import CreateGameCommand

class GameUseCase(ABC):
    @abstractmethod
    async def get_game_list(
        self,
        *,
        limit: int = 12,
        prev: int | None = None,
    ) -> list[Game]:
        """Get game list"""

    @abstractmethod
    async def create_game(self, *, command: CreateGameCommand) -> None:
        """Create Game"""

    @abstractmethod
    async def get_game_by_id(self, *, game_id: int) -> Game | None:
        """Get game by id"""

