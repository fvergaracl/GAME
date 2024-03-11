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
        # get classes Name and check if it is a valid strategy
        classes = [getattr(module, name)
                   for name in dir(module) if name[0].isupper()]
        for Class in classes:
            if not check_class_methods_and_variables(Class):
                strategies.remove(strategy)
                break
            if Class not in all_strategies_classes:
                class_instance = Class()
                # append filename as id
                class_instance.id = strategy
                all_strategies_classes.append(class_instance)

    return all_strategies_classes
