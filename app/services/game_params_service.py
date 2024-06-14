from app.repository.game_params_repository import GameParamsRepository
from app.services.base_service import BaseService


class GameParamsService(BaseService):
    """
    Service class for game parameters.

    Attributes:
        game_params_repository (GameParamsRepository): Repository instance for
         game parameters.
    """

    def __init__(self, game_params_repository: GameParamsRepository):
        """
        Initializes the GameParamsService with the provided repository.

        Args:
            game_params_repository (GameParamsRepository): The repository
              instance.
        """
        self.game_params_repository = game_params_repository
        super().__init__(game_params_repository)
