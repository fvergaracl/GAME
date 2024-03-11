import os
import importlib
from app.engine.check_base_strategy_class import (
    check_class_methods_and_variables
)


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

    all_strategies_classes = []
    for strategy in strategies:

        module = importlib.import_module(f"app.engine.{strategy}")
        classes = [getattr(module, name)
                   for name in dir(module) if name[0].isupper()]
        for Class in classes:
            if not check_class_methods_and_variables(Class):
                strategies.remove(strategy)
                break
            if Class not in all_strategies_classes:
                class_instance = Class()

                class_instance.id = strategy
                all_strategies_classes.append(class_instance)

    # delete all duplicated strategies
    all_strategies_classes = list(
        {strat.get_strategy_id(): strat for strat in
         all_strategies_classes}.values()
    )

    return all_strategies_classes
