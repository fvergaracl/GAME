from app.core.exceptions import ConflictError, NotFoundError
from app.services.base_service import BaseService
from app.engine.all_engine_strategies import all_engine_strategies
import inspect
import os


class StrategyService(BaseService):
    def __init__(self):
        self.strategy_repository = strategy_repository
        super().__init__(strategy_repository)

    def list_all_strategies(self):
        all_unclean_strategies = all_engine_strategies()
        response = []
        for strategy in all_unclean_strategies:
            file_class = inspect.getfile(strategy.__class__)
            filename_id = os.path.basename(file_class)
            filename_id = filename_id.replace(".py", "")
            response.append({
                "id": filename_id,
                "name": strategy.get_strategy_name(),
                "description": strategy.get_strategy_description(),
                "nameSlug": strategy.get_strategy_name_slug(),
                "version": strategy.get_strategy_version(),
                "variables": strategy.get_variables(),
            })
        return response

    def get_strategy_by_id(self, id):
        all_strategies = self.list_all_strategies()
        for strategy in all_strategies:
            if strategy["id"] == id:
                return strategy
        raise NotFoundError(
            detail=f"Strategy not found with id: {id}"
        )

    def create_strategy(self, schema):
        strategyName = schema.strategyName
        strategyName_exist = self.strategy_repository.read_by_column(
            column="strategyName", value=strategyName,
            not_found_raise_exception=False
        )
        if strategyName_exist:
            raise ConflictError(
                detail=(
                    f"Strategy already exist with strategyName: {strategyName}"
                )
            )
        return self.strategy_repository.create(schema)
