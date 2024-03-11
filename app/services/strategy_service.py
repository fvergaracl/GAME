from app.core.exceptions import ConflictError
from app.repository.strategy_repository import StrategyRepository
from app.services.base_service import BaseService
from app.engine.import_app_engine_modules import import_app_engine_modules

class StrategyService(BaseService):
    def __init__(self, strategy_repository: StrategyRepository):
        self.strategy_repository = strategy_repository
        super().__init__(strategy_repository)

    def list_all_strategies(self, schema):
        all_strategies = import_app_engine_modules
        pass

    def get_strategy_by_id(self, id):
        return self.strategy_repository.read_by_id(id)

    def create_strategy(self, schema):
        strategyName = schema.strategyName
        strategyName_exist = self.strategy_repository.read_by_column(
            column="strategyName", value=strategyName, not_found_raise_exception=False
        )
        if strategyName_exist:
            raise ConflictError(
                detail=(
                    f"Strategy already exist with strategyName: {strategyName}")
            )
        return self.strategy_repository.create(schema)
