from app.repository.strategy_repository import StrategyRepository

from app.services.base_service import BaseService


class StrategyService(BaseService):
    def __init__(self, strategy_repository: StrategyRepository):
        self.strategy_repository = strategy_repository
        super().__init__(strategy_repository)
