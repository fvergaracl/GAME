import os
import importlib
from app.engine.check_base_strategy_class import check_class_methods_and_variables


def all_engine_strategies():
    strategies = []
    for file in os.listdir("app/engine"):
        if (
                file.endswith(".py") and
                file != "__init__.py" and
                file != "check_base_strategy_class.py" and
                file != "all_engine_strategies.py"):
            strategy = file[:-3]
            strategies.append(strategy)

    # import all strategies and check if they are valid with check_base_strategy_class
    # if not, remove them from the list

    for strategy in strategies:
        module = importlib.import_module(f"app.engine.{strategy}")
        # get classes Name and check if it is a valid strategy
        classes = [getattr(module, name)
                   for name in dir(module) if name[0].isupper()]
        for Class in classes:
            if not check_class_methods_and_variables(Class):
                strategies.remove(strategy)
                break

    return strategies
