import os
import importlib
from app.engine.check_base_strategy_class import (
    check_class_methods_and_variables
)


def all_engine_strategies() -> list:
    """
    Scans the 'app/engine' directory for Python modules that define strategy
      classes, excluding base and utility modules. Each strategy class is
        instantiated, checked for required methods and variables, and if
          valid, added to a list with its 'id' attribute set to the module
            name. This process dynamically discovers and validates strategy
              implementations at runtime, facilitating a plug-and-play
                architecture for strategies without hardcoding their
                  references.

    **Note**: Strategies must extend a base strategy class and implement all
      required methods and variables as per :func:
      `check_class_methods_and_variables` criteria to be considered valid.

    :return: A list of instantiated and validated strategy class objects,
      each with an 'id' attribute corresponding to their module name. The
        'BaseStrategy' class, if found, is excluded from the returned list.
    :rtype: list
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
