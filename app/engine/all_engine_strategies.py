import os
import importlib
from app.engine.check_base_strategy_class import (
    check_class_methods_and_variables
)


def all_engine_strategies() -> list:
    """
    Return a list of random ingredients as strings .

    :param kind: Optional "kind" of ingredients.
    :type kind: list[str] or None
    :raise lumache.InvalidKindError: If the kind is invalid.
    :return: The ingredients list.
    :rtype: list[str]

    """
    strategies = []
    for file in os.listdir("app/engine"):
        if (
                file.endswith(".py") and
                file != "__init__.py" and
                file != "base_strategy.py" and
                file != "check_base_strategy_class.py" and
                file != "all_engine_strategies.py"):
            strategy = file[:-3]
            strategies.append(strategy)

    all_strategies_classes = []
    for strategy in strategies:
        module = importlib.import_module(f"app.engine.{strategy}")
        classes = [getattr(module, name)
                   for name in dir(module) if name[0].isupper()]
        classes = list(filter(lambda x: 'app.engine' in str(x), classes))
        for Class in classes:
            if not check_class_methods_and_variables(Class):
                strategies.remove(strategy)
                break
            if Class not in all_strategies_classes:
                class_instance = Class()

                class_instance.id = strategy
                all_strategies_classes.append(class_instance)

    # delete BaseStrategy from the list of strategies
    all_strategies_classes = list(
        filter(lambda x: x.get_strategy_id() != 'BaseStrategy',
               all_strategies_classes)
    )
    return all_strategies_classes
