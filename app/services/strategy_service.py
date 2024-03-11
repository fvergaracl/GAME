from app.core.exceptions import ConflictError
from app.repository.strategy_repository import StrategyRepository
from app.services.base_service import BaseService
from app.engine.all_engine_strategies import all_engine_strategies
import inspect


class StrategyService(BaseService):
    def __init__(self, strategy_repository: StrategyRepository):
        self.strategy_repository = strategy_repository
        super().__init__(strategy_repository)

    def list_all_strategies(self):
        all_unclean_strategies = all_engine_strategies()
        response = []
        for strategy in all_unclean_strategies:
            # id = filename
            archivo_clase = inspect.getfile(strategy)
            response.append({

                "id": archivo_clase,
                "name": strategy.get_strategy_name(),
                "description": strategy.get_strategy_description(),
                "nameSlug": strategy.get_strategy_name_slug(),
                "version": strategy.get_strategy_version(),
                "variables": strategy.get_variables(),
            })
        print(" ")
        print(" ")
        print(" ")
        print(" ")
        print(" ")
        print(response)
        print(" ")
        print(" ")
        print(" ")
        print(" ")
        print(" ")

        return response

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
