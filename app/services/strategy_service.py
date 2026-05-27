from typing import Any

from app.core.exceptions import NotFoundError
from app.engine.all_engine_strategies import all_engine_strategies
from app.services.base_service import BaseService


class StrategyService(BaseService):
    """
    Service class for managing strategies.

    Attributes:
        None
    """

    def __init__(self) -> None:
        """
        Initializes the StrategyService.
        """
        super().__init__(None)

    def list_all_strategies(self) -> list[dict[str, Any]]:
        """
        Lists all available strategies.

        Returns:
            list: A list of all strategies.
        """
        response = []
        for strategy in all_engine_strategies():
            hash_version = strategy._generate_hash_of_calculate_points()
            response.append(
                {
                    "id": strategy.id,
                    "name": strategy.get_strategy_name(),
                    "description": strategy.get_strategy_description(),
                    "version": strategy.get_strategy_version(),
                    "variables": strategy.get_variables(),
                    "hash_version": hash_version,
                }
            )
        return response

    def get_strategy_by_id(self, id) -> dict[str, Any]:
        """
        Retrieves a strategy by its ID.

        Args:
            id (str): The ID of the strategy.

        Returns:
            dict: The strategy details.

        Raises:
            NotFoundError: If the strategy is not found.
        """
        for strategy in self.list_all_strategies():
            if strategy["id"] == id:
                return strategy
        raise NotFoundError(detail=f"Strategy not found with id: {id}")

    def get_Class_by_id(self, id) -> Any:
        """
        Retrieves the instance of a strategy by its ID.

        Args:
            id (str): The ID of the strategy.

        Returns:
            object: The strategy instance.

        Raises:
            NotFoundError: If the strategy class is not found.
        """
        for strategy in all_engine_strategies():
            if strategy.id == id:
                return strategy
        raise NotFoundError(detail=f"Strategy not found with id: {id}")
