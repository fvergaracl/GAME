from app.core.exceptions import NotFoundError
from app.services.base_service import BaseService
from app.engine.all_engine_strategies import all_engine_strategies
import inspect
import os


class StrategyService(BaseService):
    def __init__(self):
        super().__init__(None)

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
                "version": strategy.get_strategy_version(),
                "variables": strategy.get_variables()
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

    def get_Class_by_id(self, id):
        all_strategies = all_engine_strategies()
        for strategy in all_strategies:
            file_class = inspect.getfile(strategy.__class__)
            filename_id = os.path.basename(file_class)
            filename_id = filename_id.replace(".py", "")
            if filename_id == id:
                return strategy
        raise NotFoundError(
            detail=f"Strategy not found with id: {id}"
        )
